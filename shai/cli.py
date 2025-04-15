import typer
from rich import print

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
    print("\n--- 🧠 [bold]Creating Context[/bold] ---")
    explanation = agent.create_context(prompt, agent.explain_prompt, False)

    print(f"\n💬 {explanation}")

    # Generate commands
    try:
        commands = agent.generate_commands(agent.command_prompt)
    except Exception as e:
        print(f"\n❌ [bold red]Error:[/bold red] Failed to generate commands: {e}")
        commands = CommandsResponse(commands=[])

    if commands.commands:
        execute_commands(commands, executor)
    else:
        print("\n❌ [bold red]Error:[/bold red] No valid commands returned.")


def execute_commands(commands: CommandsResponse, executor: ShellExecutor):
    """
    Execute the generated commands.
    """
    print("\n\n--- 🛠️ [bold]Suggested Command(s)[/bold] ---")
    for cmd in commands.commands:
        danger_symbol = "⚠️ " if cmd.dangerous else ""
        print(f"# {danger_symbol}{cmd.explanation}")
        print(f"[bold]$ {cmd.cmd}[/bold]\n")

    if typer.confirm("\n🤔 Run these command(s)?"):
        for cmd in commands.commands:
            try:
                print(f"\n--- 🏃 Running command: {cmd.cmd} ---")
                executor.run(cmd.cmd)
            except Exception as e:
                error = f"\n❌ [bold red]Error executing command '{cmd.cmd}':[/bold red] {e}"
                print(error)
                explanation = agent.create_context(error, agent.error_prompt, True)
                print(f"\n💬 {explanation}")

                try:
                    commands = agent.generate_commands(agent.error_command_prompt)
                except Exception as e:
                    print(
                        f"\n❌ [bold red]Error:[/bold red] Failed to generate commands: {e}"
                    )
                    commands = CommandsResponse(commands=[])

                if commands.commands:
                    execute_commands(commands, executor)

        # print("\n\n--- 🧹 [bold]Cleanup[/bold] ---")
        # cleanup(executor)


def cleanup(executor: ShellExecutor):
    """
    After the generated commands are ran successfully, check that the output is what was expected.
    """
    explanation = agent.create_context(agent.cleanup_prompt, None, True)
    print(f"\n💬 {explanation}")

    try:
        commands = agent.generate_commands(agent.cleanup_command_prompt)
    except Exception as e:
        print(f"\n❌ [bold red]Error:[/bold red] Failed to generate commands: {e}")
        commands = CommandsResponse(commands=[])

    if commands.commands:
        execute_commands(commands, executor)


if __name__ == "__main__":
    app()
