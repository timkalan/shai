import threading
import time
from shutil import get_terminal_size
from typing import Generator

import typer
from pynput import keyboard
from rich.align import Align
from rich.console import Console
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.text import Text

from shai.agent import Agent
from shai.shell import ShellExecutor
from shai.types import Command, CommandsResponse, DisplayCommand

app = typer.Typer()
agent = Agent()
executor = ShellExecutor()
console = Console()

# --- Globals for input handling ---
trigger_key = None
trigger_lock = threading.Lock()
abort_requested = threading.Event()


def on_press(key):
    """
    Callback function for key press events.
    Sets the trigger_key based on user input.
    """
    global trigger_key
    try:
        char = key.char
        with trigger_lock:
            if char in ["r", "a"]:
                trigger_key = char
                if char == "a":
                    abort_requested.set()
    except AttributeError:
        # Special keys (like shift, ctrl, etc.) don't have .char
        pass


keyboard_listener = keyboard.Listener(on_press=on_press)


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
    layout["upper"].split_row(Layout(name="tools"), Layout(name="thoughts"))
    return layout


def tools_panel(tools: list[str]) -> Panel:
    content = "\n".join(tools)
    return Panel(
        Text.from_markup(content),
        title="🛠 Tools",
    )


def triggers_panel(status: str = "Waiting...") -> Panel:
    content = Text.from_markup(
        "[bold cyan]r[/bold cyan] Run all\n"
        "[bold red]a[/bold red] Abort\n\n"
        f"[dim]Status: {status}[/dim]",
        justify="left",
    )
    return Panel(content, title="👤 Triggers")


def thoughts_panel(lines: list[str]) -> Panel:
    content = "\n".join(lines)
    return Panel(
        Text.from_markup(content),
        title="💭 Thoughts",
    )


def tasks_panel(commands: list[DisplayCommand]) -> Panel:
    statuses = {
        "pending": "⏳",
        "running": "🏃",
        "success": "✅",
        "error": "❌",
        "aborted": "🛑",
    }

    content = "\n\n".join(
        (
            f"# {statuses.get(cmd.status, '?')}{'⚠️' if cmd.cmd.dangerous else ''}[yellow] {cmd.cmd.explanation}[/yellow]\n[bold green]$ {cmd.cmd.cmd}[/bold green]"
            if hasattr(cmd.cmd, "explanation")
            else f"[bold green]$ {cmd}[/bold green]"
        )
        for cmd in commands
    )
    return Panel(
        # Change overflow from "fold" to "ellipsis"
        Text.from_markup(content, justify="left", overflow="ellipsis"),
        title="📜 Tasks",
    )


@app.command()
def main(prompt: str = typer.Argument(...)):
    layout = make_layout()

    term_width = get_terminal_size((80, 20)).columns
    max_width = int(term_width * 0.8)

    wrapped_layout = Align.center(
        Panel(layout, title="🤖 shai", width=max_width, height=40, border_style="dim"),
        vertical="top",
    )

    # Initial layout setup
    layout["tasks"].update(tasks_panel([]))
    layout["thoughts"].update(thoughts_panel(["[dim]Generating explanation...[/dim]"]))
    layout["tools"].update(tools_panel(["[dim]Initializing...[/dim]"]))
    layout["triggers"].update(triggers_panel("Initializing..."))

    keyboard_listener.start()

    try:
        with Live(
            wrapped_layout, auto_refresh=False, vertical_overflow="visible"
        ) as live:
            layout["triggers"].update(triggers_panel("Generating context..."))
            live.refresh()

            # Context phase
            explanation = _tools_and_explanation(
                agent.create_context(prompt, agent.explain_prompt, False), layout, live
            )

            if abort_requested.is_set():
                layout["thoughts"].update(
                    thoughts_panel(["[bold red]Aborted by user.[/bold red]"])
                )
                layout["triggers"].update(triggers_panel("Aborted."))
                return

            layout["thoughts"].update(
                thoughts_panel(
                    ["✅ [bold green]Explanation:[/bold green]", explanation]
                )
            )
            layout["triggers"].update(triggers_panel("Generating commands..."))
            layout["tasks"].update(
                tools_panel(
                    [
                        "[dim]Generating commands...[/dim]",
                    ]
                )
            )
            live.refresh()

            # Generate commands
            try:
                commands = agent.generate_commands(agent.command_prompt)
            except Exception as e:
                layout["thoughts"].update(
                    thoughts_panel([f"[bold red]Error:[/bold red] {e}"])
                )
                layout["triggers"].update(triggers_panel("Error."))
                commands = CommandsResponse(commands=[])

            if abort_requested.is_set():
                layout["thoughts"].update(
                    thoughts_panel(["[bold red]Aborted by user.[/bold red]"])
                )
                layout["triggers"].update(triggers_panel("Aborted."))
                return

            if commands.commands:
                display_commands = [
                    DisplayCommand(cmd=cmd, status="pending")
                    for cmd in commands.commands
                ]
                layout["tasks"].update(tasks_panel(display_commands))
                layout["triggers"].update(
                    triggers_panel("Waiting for user input (r/a)...")
                )
                live.refresh()

                # Wait for user input
                wait_for_user(layout, live, display_commands)

            # If no commands were generated
            else:
                display_commands = []
                layout["tasks"].update(
                    tasks_panel(
                        [
                            DisplayCommand(
                                cmd=Command(
                                    cmd="No commands generated", explanation=""
                                ),
                                status="error",
                            )
                        ]
                    )
                )
                layout["triggers"].update(triggers_panel("No commands."))

            # Keep final state visible briefly or wait for another key
            layout["triggers"].update(triggers_panel("Finished."))
            live.refresh()
            time.sleep(2)  # Keep final display for 2 seconds

    finally:
        keyboard_listener.stop()


def execute_commands(
    commands: list[DisplayCommand],
    executor: ShellExecutor,
    layout: Layout,
    live: Live,
):
    """
    Execute the generated commands.
    """
    global trigger_key

    for i in range(len(commands)):
        with trigger_lock:
            if trigger_key == "a":
                abort_requested.set()
                trigger_key = None
        if abort_requested.is_set():
            # Mark this and subsequent commands as aborted
            for j in range(i, len(commands)):
                commands[j].status = "aborted"
            layout["tasks"].update(tasks_panel(commands))
            live.refresh()
            break

        commands[i].status = "running"
        layout["tasks"].update(tasks_panel(commands))
        live.refresh()

        final_status = "success"  # Assume success initially
        error_detail = None

        try:
            # TODO: Ideally, capture stdout/stderr from executor.run
            # and potentially display it live (more complex)
            executor.run(commands[i].cmd.cmd)

            # --- Check for abort *during* execution ---
            # (pynput might catch 'a' while executor.run is blocking)
            with trigger_lock:
                if trigger_key == "a":
                    abort_requested.set()
                    trigger_key = None  # Reset trigger
            if abort_requested.is_set():
                final_status = "aborted"

        except Exception as e:
            # If abort was requested during exception, prioritize abort status
            if abort_requested.is_set():
                final_status = "aborted"
            else:
                final_status = "error"
                error_detail = e

        commands[i].status = final_status
        layout["tasks"].update(tasks_panel(commands))

        # Update thoughts panel only on error
        if final_status == "error" and error_detail:
            error_msg = (
                f"Error executing command '{commands[i].cmd.cmd}': {error_detail}"
            )
            layout["thoughts"].update(
                thoughts_panel([f"❌ [bold red]Error:[/bold red] {error_msg}"])
            )
            # Update trigger status immediately on error
            layout["triggers"].update(triggers_panel("Error occurred."))

        live.refresh()

        if final_status == "error" or final_status == "aborted":
            # If aborted, mark remaining tasks as aborted
            if final_status == "aborted":
                for j in range(i + 1, len(commands)):
                    commands[j].status = "aborted"
                layout["tasks"].update(tasks_panel(commands))
                live.refresh()
            break

    final_trigger_status = (
        "Aborted." if abort_requested.is_set() else "Execution finished."
    )
    # Avoid overwriting "Error occurred." if that was the last state
    if commands and commands[-1].status != "error":
        layout["triggers"].update(triggers_panel(final_trigger_status))
        live.refresh()


def _tools_and_explanation(
    generator: Generator[str, None, str], layout: Layout, live: Live
) -> str:
    """
    Prints live-updating tools and thoughts while building context.
    Checks for abort signal.
    """
    tools_state = []

    explanation = ""
    while True:
        # Check for abort signal during generation
        if abort_requested.is_set():
            explanation = "[Aborted during generation]"
            break

        try:
            # Use a small timeout or non-blocking check if possible,
            # but next() will block here until the generator yields.
            # Abort check relies on 'a' being pressed *before* this point
            # or during a pause in the generator's execution.
            tool_call = next(generator)
            tools_state.append(tool_call)
            layout["tools"].update(tools_panel(tools_state))
            live.refresh()

        except StopIteration as e:
            explanation = e.value
            break
        except Exception as e:
            explanation = f"[Error during generation: {e}]"
            layout["thoughts"].update(
                thoughts_panel([f"❌ [bold red]Error:[/bold red] {explanation}"])
            )
            break

    if not tools_state:
        tools_state = ["[dim]No tools used.[/dim]"]
        layout["tools"].update(tools_panel(tools_state))
        live.refresh()

    return explanation


def wait_for_user(layout: Layout, live: Live, display_commands: list[DisplayCommand]):
    """
    Wait for user input to either run or abort the commands.
    """
    global trigger_key

    user_action = None
    while user_action is None:
        with trigger_lock:
            if trigger_key:
                user_action = trigger_key
                trigger_key = None
        if user_action:
            break
        time.sleep(0.1)

    if user_action == "a" or abort_requested.is_set():
        layout["thoughts"].update(
            thoughts_panel(["[bold red]Aborted by user.[/bold red]"])
        )
        layout["triggers"].update(triggers_panel("Aborted."))
        # Mark tasks as aborted
        for cmd in display_commands:
            cmd.status = "aborted"
        layout["tasks"].update(tasks_panel(display_commands))
        return

    elif user_action == "r":
        layout["triggers"].update(triggers_panel("Executing..."))
        live.refresh()
        execute_commands(display_commands, executor, layout, live)


if __name__ == "__main__":
    abort_requested.clear()
    app()
