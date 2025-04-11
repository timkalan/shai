import subprocess

import typer

from shai.agent import Agent

app = typer.Typer()
agent = Agent()


@app.command()
def shai(prompt: str):
    """
    Ask shai to generate shell commands from natural language.
    """
    message = " ".join(prompt)
    commands_response = agent.ask(message)

    if commands_response.commands:
        if typer.confirm("\nRun these command(s)?"):
            for cmd in commands_response.commands:
                subprocess.run(cmd.cmd, shell=True)
    else:
        print("No valid commands returned.")


if __name__ == "__main__":
    app()
