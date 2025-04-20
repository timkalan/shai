from typing import List
from pydantic import BaseModel


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


class DisplayCommand(BaseModel):
    """
    A class to represent a command with its status for display purposes.
    """

    cmd: Command
    status: str  # pending, running, success, error
