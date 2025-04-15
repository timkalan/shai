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
    additional_prompt = agent.initial_prompt
    while True:
        try:
            explanation, tool_calls = agent.create_context(prompt, additional_prompt)
        except Exception as e:
            print(f"\n❌ [bold red]Error:[/bold red] {e}")
            return

        if not tool_calls:
            break

        # TODO: print the explanation only in verbose mode
        # print(f"💬 {explanation}")
        for tool_call in tool_calls:
            print(
                f"🔧 [bold]Tool:[/bold] {tool_call.function.name}({tool_call.function.arguments})"
            )

        # Run the tools
        try:
            agent.run_tools(tool_calls)
        except Exception as e:
            print(f"\n❌ [bold red]Error:[/bold red] {e}")
            return

        if not additional_prompt:
            additional_prompt = agent.explain_prompt

    # If no tool calls were made, we print the explanation
    print(f"\n💬 {explanation}")

    # Generate commands
    try:
        commands = agent.generate_commands()
    except Exception as e:
        print(f"\n❌ [bold red]Error:[/bold red] Failed to generate commands: {e}")
        commands = CommandsResponse(commands=[])

    if commands.commands:
        execute_commands(commands, executor)
    else:
        print("\n❌ [bold red]Error:[/bold red] No valid commands returned.")


def execute_commands(commands: CommandsResponse, executor: ShellExecutor):
    print("\n\n--- 🛠️ [bold]Suggested Command(s)[/bold] ---")
    for cmd in commands.commands:
        danger_symbol = "⚠️ " if cmd.dangerous else ""
        print(f"# {danger_symbol}{cmd.explanation}\n")
        print(f"[bold]$ {cmd.cmd}[/bold]\n")

    if typer.confirm("\n🤔 Run these command(s)?"):
        for cmd in commands.commands:
            try:
                executor.run(cmd.cmd)
            except Exception as e:
                print(f"[bold red]Error executing command '{cmd.cmd}':[/bold red] {e}")


if __name__ == "__main__":
    app()
