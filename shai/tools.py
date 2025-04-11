import subprocess
from typing import List

from openai.types.chat import ChatCompletionToolParam

TOOL_DEFINITIONS: List[ChatCompletionToolParam] = [
    {
        "type": "function",
        "function": {
            "name": "get_ls_output",
            "description": "Get the contents of the current directory.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_man_page",
            "description": "Get the man page for a given command.",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {"type": "string"},
                },
                "required": ["command"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_tldr_page",
            "description": "Get TLDR page for a command.",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {"type": "string"},
                },
                "required": ["command"],
            },
        },
    },
]


def run_tool(name: str, args: dict) -> str:
    """
    Run the specified tool with the given arguments.
    """
    if name == "get_ls_output":
        return subprocess.run(["ls", "-la"], capture_output=True, text=True).stdout
    elif name == "get_man_page":
        return subprocess.run(
            ["man", args["command"]], capture_output=True, text=True
        ).stdout
    elif name == "get_tldr_page":
        return subprocess.run(
            ["tldr", args["command"]], capture_output=True, text=True
        ).stdout
    else:
        return f"[unknown tool: {name}]"
