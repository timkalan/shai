import threading

import typer

from shai.agent import Agent, CommandsResponse
from shai.shell import ShellExecutor

app = typer.Typer()
agent = Agent()
executor = ShellExecutor()


@app.command()
def main(prompt: str = typer.Argument(...)):
    """
    Ask shai to generate shell commands from natural language.
    """
    stream_thread = threading.Thread(target=stream_explanation, args=(agent, prompt))
    stream_thread.start()

    try:
        commands = agent.generate_commands(prompt)
    except Exception as e:
        print(f"\nError: Failed to generate commands: {e}")
        commands = CommandsResponse(commands=[])

    stream_thread.join()

    if commands.commands:
        execute_commands(commands, executor)
    else:
        print("No valid commands returned.")


def stream_explanation(agent: Agent, message: str):
    for chunk in agent.explain(message):
        typer.echo(chunk, nl=False)


def execute_commands(commands: CommandsResponse, executor: ShellExecutor):
    typer.echo("\n\n--- Suggested Command(s) ---")
    for cmd in commands.commands:
        danger_symbol = "⚠️ " if cmd.dangerous else ""
        typer.echo(f"# {danger_symbol}{cmd.explanation}\n$ {cmd.cmd}\n")

    if typer.confirm("\nRun these command(s)?"):
        for cmd in commands.commands:
            executor.run(cmd.cmd)


if __name__ == "__main__":
    app()
