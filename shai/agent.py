import threading
from pathlib import Path
from typing import Generator, List

from openai import OpenAI
from pydantic import BaseModel

from shai.config import Config


class Command(BaseModel):
    """
    A class to represent a shell command with its explanation and danger level.
    """

    cmd: str
    explanation: str
    dangerous: bool = False


class CommandsResponse(BaseModel):
    """
    A class to represent a response containing a list of commands.
    """

    commands: List[Command]


class Agent:
    """
    A simple class to interact with OpenAI's API.
    """

    def __init__(self):

        config = Config()

        self.client = OpenAI(
            api_key=config.api_key,
            base_url=config.base_url,
        )
        self.model = config.model
        self.command_prompt = self._load_prompt("shai/prompts/command_prompt.txt")
        self.explain_prompt = self._load_prompt("shai/prompts/explain_prompt.txt")

    def _load_prompt(self, path: str) -> str:
        """
        Load a prompt from a file.
        """
        return Path(path).read_text().strip()

    def ask(self, message: str) -> CommandsResponse:
        """
        Stream a natural-language explanation while generating shell commands.
        """

        # Start streaming explanation in a thread
        def stream_task():
            for chunk in self.explain(message):
                print(chunk, end="", flush=True)

        stream_thread = threading.Thread(target=stream_task)
        stream_thread.start()

        # Generate structured commands in main thread
        try:
            commands = self.generate_commands(message)
        except Exception as e:
            print(f"\nError: Failed to generate commands: {e}")
            commands = CommandsResponse(commands=[])

        # Wait for stream to finish
        stream_thread.join()

        print("\n\n--- Suggested Command(s) ---")
        for cmd in commands.commands:
            print(f"$ {cmd.cmd}\n# {cmd.explanation}")
        return commands

    def explain(self, message: str) -> Generator[str, None, None]:
        """
        Send a message to the OpenAI API and stream the response to stdout.
        """
        try:
            stream = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.explain_prompt},
                    {"role": "user", "content": message},
                ],
                stream=True,
            )
            for chunk in stream:
                content = chunk.choices[0].delta.content
                if content:
                    yield content
        except Exception as e:
            raise RuntimeError(f"LLM call failed: {e}") from e

    def generate_commands(self, message: str) -> CommandsResponse:
        """
        Send a message to the OpenAI API and return the response as JSON string.
        """
        try:
            response = self.client.beta.chat.completions.parse(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.command_prompt},
                    {"role": "user", "content": message},
                ],
                response_format=CommandsResponse,
            )
            content = response.choices[0].message.parsed
            if content:
                return content
            raise ValueError("No content returned from the LLM.")
        except Exception as e:
            raise RuntimeError(f"LLM call failed: {e}") from e
