import json
from pathlib import Path
from typing import Generator, List, Tuple

from openai import OpenAI
from openai.types.chat import (
    ChatCompletionAssistantMessageParam,
    ChatCompletionFunctionMessageParam,
    ChatCompletionMessageParam,
    ChatCompletionMessageToolCall,
    ChatCompletionMessageToolCallParam,
)

from shai.config import Config
from shai.tools import TOOL_DEFINITIONS, run_tool
from shai.types import CommandsResponse


class Agent:
    """
    A simple class to interact with OpenAI's API.
    """

    def __init__(self):

        config = Config()

        self.client: OpenAI = OpenAI(
            api_key=config.api_key,
            base_url=config.base_url,
        )
        self.model: str = config.model
        self.command_prompt: str = self._load_prompt("shai/prompts/command_prompt.txt")
        self.initial_prompt: str = self._load_prompt("shai/prompts/initial_prompt.txt")
        self.explain_prompt: str = self._load_prompt("shai/prompts/explain_prompt.txt")
        self.error_prompt: str = self._load_prompt("shai/prompts/error_prompt.txt")
        self.error_command_prompt: str = self._load_prompt(
            "shai/prompts/error_command_prompt.txt"
        )
        self.cleanup_prompt: str = self._load_prompt("shai/prompts/cleanup_prompt.txt")
        self.cleanup_command_prompt: str = self._load_prompt(
            "shai/prompts/cleanup_command_prompt.txt"
        )

        self.messages: list[ChatCompletionMessageParam] = [
            {"role": "system", "content": self.initial_prompt},
        ]

    def _load_prompt(self, path: str) -> str:
        """
        Load a prompt from a file.
        """
        return Path(path).read_text().strip()

    def get_context(
        self, additional_prompt: str | None
    ) -> Tuple[str, List[ChatCompletionMessageToolCall]]:
        """
        Create the context by calling any potetially relevant tools.
        Also returns the thought process. Can take an additional prompt.
        """
        if additional_prompt:
            self.messages.append({"role": "user", "content": additional_prompt})

        response = self.client.chat.completions.create(
            model=self.model,
            messages=self.messages,
            tools=TOOL_DEFINITIONS,
            tool_choice="auto",
        )

        explanation = response.choices[0].message.content or ""
        tool_calls = response.choices[0].message.tool_calls or []

        # TODO: ChatGPT told me to do this, but it seems hacky.
        # Convert to the correct param typ
        tool_call_params: list[ChatCompletionMessageToolCallParam] = [
            {
                "id": call.id,
                "function": {
                    "name": call.function.name,
                    "arguments": call.function.arguments,
                },
                "type": call.type,
            }
            for call in tool_calls
        ]

        self.messages.append(
            ChatCompletionAssistantMessageParam(
                role="assistant",
                content=explanation,
                tool_calls=tool_call_params,
            )
        )

        return explanation, tool_calls

    def create_context(
        self, message: str, additional_prompt: str | None, begin_with_prompt: bool
    ) -> Generator[str, None, str]:
        """
        Run get_context until no more tools are called.
        Yields tool information and returns the explanation.
        """
        self.messages.append({"role": "user", "content": message})

        insert_prompt = begin_with_prompt
        while True:
            if insert_prompt:
                explanation, tool_calls = self.get_context(additional_prompt)
            else:
                explanation, tool_calls = self.get_context(None)
                insert_prompt = True

            if not tool_calls:
                break

            # Run the tools
            try:
                for tool_info in self.run_tools(tool_calls):
                    yield tool_info
            except Exception as e:
                raise RuntimeError(f"Failed to run tools: {e}") from e

        return explanation

    def run_tools(
        self, tool_calls: List[ChatCompletionMessageToolCall]
    ) -> Generator[str, None, None]:
        """
        Run the tools and yield the results.
        """
        for call in tool_calls:
            try:
                args = json.loads(call.function.arguments)
                tool_output = run_tool(call.function.name, args)
            except Exception as e:
                tool_output = f"Error running tool '{call.function.name}': {str(e)}"
                raise RuntimeError(
                    f"Failed to run tool '{call.function.name}': {e}"
                ) from e

            tool_message: ChatCompletionFunctionMessageParam = {
                "content": tool_output,
                "role": "function",
                "name": call.function.name,
            }

            self.messages.append(tool_message)

            yield f"🔧 Tool: {call.function.name}({call.function.arguments})"

    def generate_commands(self, prompt: str) -> CommandsResponse:
        """
        Send a message to the OpenAI API and return the response as JSON string.
        """
        try:
            response = self.client.beta.chat.completions.parse(
                model=self.model,
                messages=self.messages
                + [
                    {"role": "user", "content": prompt},
                ],
                response_format=CommandsResponse,
            )
            content = response.choices[0].message.parsed
            if content:
                self.messages.append(
                    ChatCompletionAssistantMessageParam(
                        role="assistant",
                        content=str(content),
                    )
                )
                return content
            raise ValueError("No content returned from the LLM.")
        except Exception as e:
            raise RuntimeError(f"LLM call failed: {e}") from e
