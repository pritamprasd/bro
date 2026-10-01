"""Rich Console UI for live log streaming, thoughts, and action breadcrumbs."""

from typing import Optional
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.rule import Rule
from rich.theme import Theme

custom_theme = Theme({
    "info": "cyan",
    "warning": "yellow",
    "danger": "bold red",
    "success": "bold green",
    "thought": "italic #89b4fa",
    "action": "bold #fab387",
    "step": "bold #cba6f7",
})

class BroConsole:
    def __init__(self, output_mode: str = "both"):
        self.output_mode = output_mode
        self.console = Console(theme=custom_theme)

    def is_cli_enabled(self) -> bool:
        return self.output_mode in ["both", "cli"]

    def banner(self) -> None:
        if not self.is_cli_enabled():
            return
        self.console.print(
            Panel(
                "[bold cyan]🤖 BRO AI ASSISTANT[/bold cyan]\n"
                "[dim]Vision Desktop & Web Automation Engine | Local & Cloud Hybrid[/dim]",
                border_style="cyan",
                expand=False,
            )
        )

    def step(self, step_num: int, total_steps: int, description: str) -> None:
        if not self.is_cli_enabled():
            return
        self.console.print(f"\n[step]▶ Step {step_num}/{total_steps}:[/step] [bold]{description}[/bold]")

    def thought(self, text: str) -> None:
        if not self.is_cli_enabled():
            return
        self.console.print(f"[thought]💭 {text}[/thought]")

    def action(self, actuator: str, detail: str) -> None:
        if not self.is_cli_enabled():
            return
        self.console.print(f"[action]⚡ [{actuator.upper()}][/action] {detail}")

    def success(self, text: str) -> None:
        if not self.is_cli_enabled():
            return
        self.console.print(f"[success]✔ {text}[/success]")

    def warning(self, text: str) -> None:
        if not self.is_cli_enabled():
            return
        self.console.print(f"[warning]⚠ {text}[/warning]")

    def error(self, text: str) -> None:
        if not self.is_cli_enabled():
            return
        self.console.print(f"[danger]✖ {text}[/danger]")

    def response(self, text: str) -> None:
        if not self.is_cli_enabled():
            return
        self.console.print(Rule(style="cyan"))
        self.console.print(Markdown(text))
        self.console.print(Rule(style="cyan"))
