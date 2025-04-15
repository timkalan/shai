import subprocess
from typing import List

from openai.types.chat import ChatCompletionToolParam

TOOL_DEFINITIONS: List[ChatCompletionToolParam] = [
    {
        "type": "function",
        "function": {
            "name": "get_ls_output",
            "description": "Get the contents of a directory using 'ls -la'.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Path to the directory. Defaults to the current directory.",
                        "default": ".",
                    }
                },
                "required": ["path"],
            },
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
    {
        "type": "function",
        "function": {
            "name": "read_file_head",
            "description": "Read the first lines of a file to help determine its structure.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Path to the file"},
                    "num_lines": {
                        "type": "integer",
                        "description": "Number of lines to read from the top (default 20)",
                        "default": 20,
                    },
                },
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "stat_file",
            "description": "Get metadata about a file or directory.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Path to the file or directory",
                    },
                },
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_files",
            "description": "Find files with names matching a pattern.",
            "parameters": {
                "type": "object",
                "properties": {
                    "pattern": {
                        "type": "string",
                        "description": "Pattern to search (e.g., *.log)",
                    },
                    "path": {
                        "type": "string",
                        "description": "Where to start searching",
                        "default": ".",
                    },
                },
                "required": ["pattern"],
            },
        },
    },
]


def run_tool(name: str, args: dict) -> str:
    """
    Run the specified tool with the given arguments.
    """
    if name == "get_ls_output":
        path = args.get("path", ".")
        return subprocess.run(
            ["ls", "-la", path], capture_output=True, text=True
        ).stdout
    elif name == "get_man_page":
        return subprocess.run(
            ["man", args["command"]], capture_output=True, text=True
        ).stdout
    elif name == "get_tldr_page":
        return subprocess.run(
            ["tldr", args["command"]], capture_output=True, text=True
        ).stdout
    elif name == "read_file_head":
        num_lines = str(args.get("num_lines", 20))
        return subprocess.run(
            ["head", f"-n{num_lines}", args["path"]], capture_output=True, text=True
        ).stdout
    elif name == "stat_file":
        return subprocess.run(
            ["stat", args["path"]], capture_output=True, text=True
        ).stdout
    elif name == "search_files":
        return subprocess.run(
            ["find", args.get("path", "."), "-name", args["pattern"]],
            capture_output=True,
            text=True,
        ).stdout

    else:
        return f"[unknown tool: {name}]"
