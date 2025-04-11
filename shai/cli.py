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
    # Create context by calling any potentially relevant tools
    typer.echo("\n--- 🧠 Creating Context ---")
    tool_calls = agent.create_context(prompt)
    for tool_call in tool_calls:
        typer.echo(f"🔧 Tool: {tool_call.function.name}")

    try:
        agent.run_tools(tool_calls)
        typer.echo("\n--- ✅ Context Created ---")
    except Exception as e:
        typer.echo(f"\n❌ Error: Failed to run tools: {e}")
        return

    # Stream an explanation
    stream_thread = threading.Thread(target=stream_explanation, args=(agent,))
    stream_thread.start()

    # Generate commands
    try:
        commands = agent.generate_commands()
    except Exception as e:
        typer.echo(f"\n❌ Error: Failed to generate commands: {e}")
        commands = CommandsResponse(commands=[])

    stream_thread.join()

    if commands.commands:
        execute_commands(commands, executor)
    else:
        typer.echo("\n❌ Error: No valid commands returned.")


def stream_explanation(agent: Agent):
    for chunk in agent.explain():
        typer.echo(chunk, nl=False)


def execute_commands(commands: CommandsResponse, executor: ShellExecutor):
    typer.echo("\n\n--- 🔧 Suggested Command(s) ---")
    for cmd in commands.commands:
        danger_symbol = "⚠️ " if cmd.dangerous else ""
        typer.echo(f"# {danger_symbol}{cmd.explanation}\n$ {cmd.cmd}\n")

    if typer.confirm("\n🤔 Run these command(s)?"):
        for cmd in commands.commands:
            try:
                executor.run(cmd.cmd)
            except Exception as e:
                typer.echo(f"Error executing command '{cmd.cmd}': {e}")


if __name__ == "__main__":
    app()
