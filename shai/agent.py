import json
from pathlib import Path
from typing import List, Tuple

from openai import OpenAI
from openai.types.chat import (
    ChatCompletionAssistantMessageParam,
    ChatCompletionFunctionMessageParam,
    ChatCompletionMessageParam,
    ChatCompletionMessageToolCall,
    ChatCompletionMessageToolCallParam,
)

from shai.config import Config
from shai.tools import run_tool, TOOL_DEFINITIONS
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
        self.explain_prompt: str = self._load_prompt("shai/prompts/explain_prompt.txt")
        self.initial_prompt: str = self._load_prompt("shai/prompts/initial_prompt.txt")

        self.messages: list[ChatCompletionMessageParam] = []

    def _load_prompt(self, path: str) -> str:
        """
        Load a prompt from a file.
        """
        return Path(path).read_text().strip()

    def create_context(
        self, message: str, additional_prompt: str | None
    ) -> Tuple[str, List[ChatCompletionMessageToolCall]]:
        """
        Create the context by calling any potetially relevant tools.
        Also returns the thought process. Can take an additional prompt.
        """
        if additional_prompt:
            self.messages.append({"role": "user", "content": additional_prompt})

        self.messages.append({"role": "user", "content": message})

        response = self.client.chat.completions.create(
            model=self.model,
            messages=self.messages,
            tools=TOOL_DEFINITIONS,
            tool_choice="auto",
        )

        explanation = response.choices[0].message.content or ""
        self.messages.append(
            ChatCompletionAssistantMessageParam(
                role="assistant",
                content=explanation,
            )
        )

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
                content=response.choices[0].message.content,
                tool_calls=tool_call_params,
            )
        )

        return explanation, tool_calls

    def run_tools(self, tool_calls: List[ChatCompletionMessageToolCall]):
        """
        Run the tools and return the results.
        """
        tool_messages: List[ChatCompletionFunctionMessageParam] = []
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

            tool_messages.append(tool_message)

        self.messages.extend(tool_messages)

        if len(tool_calls) != len(tool_messages):
            raise RuntimeError("Mismatch between tool calls and tool responses!")

    def generate_commands(self) -> CommandsResponse:
        """
        Send a message to the OpenAI API and return the response as JSON string.
        """
        try:
            response = self.client.beta.chat.completions.parse(
                model=self.model,
                messages=self.messages
                + [
                    {"role": "user", "content": self.command_prompt},
                ],
                response_format=CommandsResponse,
            )
            content = response.choices[0].message.parsed
            if content:
                return content
            raise ValueError("No content returned from the LLM.")
        except Exception as e:
            raise RuntimeError(f"LLM call failed: {e}") from e
