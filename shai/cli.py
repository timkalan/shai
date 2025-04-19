from dataclasses import dataclass
from shutil import get_terminal_size
from typing import Generator

import typer
from rich import print
from rich.align import Align
from rich.console import Console
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.text import Text

from shai.agent import Agent
from shai.types import CommandsResponse, Command
from shai.shell import ShellExecutor

app = typer.Typer()
agent = Agent()
executor = ShellExecutor()
console = Console()


@dataclass()
class DisplayCommand:
    cmd: Command
    status: str  # pending, running, success, error


def make_layout() -> Layout:
    layout = Layout()
    layout.split_row(
        Layout(name="triggers", ratio=1),
        Layout(name="main", ratio=4),
    )

    layout["main"].split(
        Layout(name="upper", ratio=1),
        Layout(name="tasks", ratio=1),
    )
    # layout.split(Layout(name="upper", ratio=1), Layout(name="tasks", ratio=1))

    layout["upper"].split_row(Layout(name="tools"), Layout(name="thoughts"))
    return layout


def tools_panel(tools: list[str]) -> Panel:
    content = "\n".join(tools)
    return Panel(
        Text.from_markup(content),
        title="🛠 Tools",
    )


def triggers_panel(triggers: list[str]) -> Panel:
    content = "\n".join(triggers)
    # content = Text.from_markup(
    #     "[bold cyan][r][/bold cyan] Run all\n[bold red][a][/bold red] Abort",
    #     justify="left",
    # )
    return Panel(Text.from_markup(content), title="🎛️ Triggers")


def thoughts_panel(lines: list[str]) -> Panel:
    content = "\n".join(lines)
    return Panel(
        Text.from_markup(content),
        title="💭 Thoughts",
    )


def tasks_panel(commands: list[DisplayCommand]) -> Panel:
    statuses = {
        "pending": "[bold yellow]Pending...[/bold yellow]",
        "running": "[bold blue]Running...[/bold blue]",
        "success": "[bold green]Success![/bold green]",
        "error": "[bold red]Error![/bold red]",
    }

    content = "\n\n".join(
        (
            f"\n# {statuses[cmd.status]}\n[yellow]# {cmd.cmd.explanation}[/yellow]\n[bold green]$ {cmd.cmd.cmd}[/bold green]"
            if hasattr(cmd.cmd, "explanation")
            else f"[bold green]$ {cmd}[/bold green]"
        )
        for cmd in commands
    )
    return Panel(
        Text.from_markup(content, justify="left", overflow="fold"),
        title="📜 Tasks",
        # border_style="green",
    )


@app.command()
def main(prompt: str = typer.Argument(...)):
    """
    Ask shai to generate shell commands from natural language.
    """
    layout = make_layout()

    # Set a target width
    term_width = get_terminal_size((80, 20)).columns
    max_width = int(term_width * 0.8)

    layout["tasks"].update(tasks_panel([]))
    layout["thoughts"].update(thoughts_panel([]))
    # layout["triggers"].update(triggers_panel([]))

    wrapped_layout = Align.center(
        Panel(layout, title="🤖 shai", width=max_width, height=40, border_style="dim"),
        vertical="top",
    )

    with Live(wrapped_layout, refresh_per_second=5):

        # Context phase
        explanation = _tools_and_explanation(
            agent.create_context(prompt, agent.explain_prompt, False), layout
        )

        # Show explanation in thoughts
        layout["thoughts"].update(
            thoughts_panel(["✅ [bold green]Explanation:[/bold green]", explanation])
        )

        # Generate commands
        try:
            commands = agent.generate_commands(agent.command_prompt)
        except Exception as e:
            layout["thoughts"].update(
                thoughts_panel([f"❌ [bold red]Error:[/bold red] {e}"])
            )
            commands = CommandsResponse(commands=[])

        if commands.commands:
            layout["tasks"].update(
                tasks_panel(
                    [
                        DisplayCommand(cmd=cmd, status="pending")
                        for cmd in commands.commands
                    ]
                )
            )

        else:
            print("\n❌ [bold red]Error:[/bold red] No valid commands returned.")

        execute_commands(commands, executor, layout)


def execute_commands(
    commands: CommandsResponse, executor: ShellExecutor, layout: Layout
):
    """
    Execute the generated commands.
    """
    if typer.confirm("\n🤔 Run these command(s)?"):
        for cmd in commands.commands:
            try:
                layout["tasks"].update(
                    tasks_panel(
                        [
                            DisplayCommand(cmd=cmd, status="running"),
                        ]
                    )
                )
                executor.run(cmd.cmd)
                layout["tasks"].update(
                    tasks_panel(
                        [
                            DisplayCommand(cmd=cmd, status="success"),
                        ]
                    )
                )
            except Exception as e:
                layout["tasks"].update(
                    tasks_panel(
                        [
                            DisplayCommand(cmd=cmd, status="error"),
                        ]
                    )
                )
                error = f"\n❌ [bold red]Error executing command '{cmd.cmd}':[/bold red] {e}"
                print(error)
                gen = agent.create_context(error, agent.error_prompt, True)
                while True:
                    try:
                        tool_call = next(gen)
                        print(tool_call)
                    except StopIteration as e:
                        explanation = e.value
                        break
                print(f"\n💬 {explanation}")

                try:
                    commands = agent.generate_commands(agent.error_command_prompt)
                except Exception as e:
                    print(
                        f"\n❌ [bold red]Error:[/bold red] Failed to generate commands: {e}"
                    )
                    commands = CommandsResponse(commands=[])

                if commands.commands:
                    execute_commands(commands, executor, layout)

        # print("\n\n--- 🧹 [bold]Cleanup[/bold] ---")
        # cleanup(executor)


def _tools_and_explanation(generator: Generator[str, None, str], layout: Layout) -> str:
    """
    Prints live-updating tools and thoughts while building context.
    """
    tools_state = []
    layout["tools"].update(tools_panel(tools_state))

    while True:
        try:
            tool_call = next(generator)
            tools_state.append(tool_call)
            layout["tools"].update(tools_panel(tools_state))
        except StopIteration as e:
            explanation = e.value
            break

    return explanation


# def cleanup(executor: ShellExecutor):
#     """
#     After the generated commands are ran successfully, check that the output is what was expected.
#     """
#     explanation = agent.create_context(agent.cleanup_prompt, None, True)
#     print(f"\n💬 {explanation}")
#
#     try:
#         commands = agent.generate_commands(agent.cleanup_command_prompt)
#     except Exception as e:
#         print(f"\n❌ [bold red]Error:[/bold red] Failed to generate commands: {e}")
#         commands = CommandsResponse(commands=[])
#
#     if commands.commands:
#         execute_commands(commands, executor)


if __name__ == "__main__":
    app()
