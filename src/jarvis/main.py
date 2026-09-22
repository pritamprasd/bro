"""Main CLI entrypoint for Jarvis Phase 2."""

import sys
from typing import List, Optional
import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from jarvis.actuators.cdp_browser import CDPBrowserActuator
from jarvis.config import JarvisConfig, load_config, save_config
from jarvis.core.agent import JarvisAgent
from jarvis.core.audit import AuditManager
from jarvis.core.supervisor import Supervisor
from jarvis.security.vault import SecretVault

app = typer.Typer(
    help="Jarvis: Autonomous Personal AI Assistant for Linux X11 Desktop & Web.",
    no_args_is_help=True,
)
console = Console()

@app.command()
def run(
    goal: str = typer.Argument(..., help="The task or goal for Jarvis to execute"),
    file: Optional[List[str]] = typer.Option(
        None, "--file", "-f", help="Attach resource files needed for the task"
    ),
    autonomous: Optional[bool] = typer.Option(
        None, "--autonomous", "-a", help="Run without asking for confirmation on high-stakes actions"
    ),
    policy: Optional[str] = typer.Option(
        None, "--policy", "-p", help="Model policy: 'local_only', 'tier_fallback', 'cloud_only'"
    ),
    output_mode: Optional[str] = typer.Option(
        None, "--output", "-o", help="Output mode: 'both', 'cli', 'voice'"
    ),
):
    """Execute a task via Jarvis."""
    config = load_config()

    if autonomous is not None:
        config.autonomous_mode = autonomous
    if policy:
        config.model.policy = policy  # type: ignore
    if output_mode:
        config.output_mode = output_mode  # type: ignore

    agent = JarvisAgent(config)
    agent.run_task(goal, file_paths=file)

@app.command()
def voice(
    duration: int = typer.Option(5, "--duration", "-d", help="Recording duration in seconds"),
    autonomous: bool = typer.Option(False, "--autonomous", "-a", help="Enable autonomous mode"),
):
    """Interact with Jarvis via voice (Speech-to-Text & Text-to-Speech)."""
    config = load_config()
    config.autonomous_mode = autonomous
    from jarvis.voice.stt import SpeechToText

    console.print("[bold cyan]🎙️ Jarvis Voice Interface Active[/bold cyan]")
    console.print(f"[dim]Recording for {duration} seconds... Speak your command now:[/dim]")

    stt = SpeechToText(config.voice)
    try:
        spoken_text = stt.record_and_transcribe(duration_seconds=duration)
    except Exception as e:
        console.print(f"[bold red]Speech recording failed:[/bold red] {e}")
        raise typer.Exit(1)

    if not spoken_text.strip():
        console.print("[yellow]No speech detected. Please try again.[/yellow]")
        raise typer.Exit(0)

    console.print(f"\n[bold green]Recognized Command:[/bold green] \"{spoken_text}\"\n")
    agent = JarvisAgent(config)
    agent.run_task(spoken_text)

@app.command()
def brief():
    """Trigger the Daily brief on demand."""
    config = load_config()
    from jarvis.watchdogs.cron_engine import CronEngine
    from jarvis.voice.tts import TextToSpeech
    tts = TextToSpeech(config.voice)
    engine = CronEngine(config.watchdogs.cron, briefing_callback=lambda b: tts.speak(b))
    msg = engine.trigger_brief()
    console.print(Panel(msg, title="[bold cyan]☀️ Jarvis Mark 1 Daily Brief[/bold cyan]", border_style="cyan"))

# System Lifecycle Commands (Start, Stop, Status)
@app.command()
def start():
    """Start all Jarvis background services (Web UI, Spotlight Bar, Telegram Bot, Watchdogs)."""
    supervisor = Supervisor()
    res = supervisor.start()
    if res["status"] == "already_running":
        console.print("[yellow]Jarvis is already running.[/yellow]")
    else:
        console.print("[bold green]✔ Jarvis Mark 1 System Online![/bold green]")
        console.print(f"[cyan]Local HUD Dashboard:[/cyan]   [bold underline]{res.get('web_url', 'http://localhost:8765')}[/bold underline]")
        if res.get("network_url"):
            console.print(f"[cyan]Mobile / Network HUD:[/cyan] [bold underline]{res.get('network_url')}[/bold underline]")
        console.print("[dim]Spotlight Bar active: Press Alt+J anywhere on desktop.[/dim]")

@app.command()
def stop():
    """Trigger Master Kill-Switch to cleanly terminate all running Jarvis services."""
    supervisor = Supervisor()
    res = supervisor.stop()
    console.print("[bold red]🛑 Master Kill-Switch Activated:[/bold red] All Jarvis Mark 1 services terminated.")
    for p in res.get("processes", []):
        console.print(f"  [dim]• Terminated {p}[/dim]")

@app.command()
def status():
    """Check status of Jarvis supervisor and running components."""
    supervisor = Supervisor()
    stat = supervisor.status()
    if stat.get("running"):
        console.print("[bold green]● Jarvis System Status: ONLINE[/bold green]")
        console.print(f"  Local HUD:   {stat.get('web_url')}")
        if stat.get("network_url"):
            console.print(f"  Mobile / Network HUD: {stat.get('network_url')}")
        pids = stat.get("pids", {})
        for k, v in pids.items():
            console.print(f"  • {k}: PID {v}")
    else:
        console.print("[bold yellow]○ Jarvis System Status: OFFLINE[/bold yellow]")

@app.command()
def cdp():
    """Launch user's everyday browser (Chrome/Brave) with CDP remote debugging on port 9222."""
    config = load_config()
    browser = CDPBrowserActuator(port=config.browser.cdp_port)
    console.print("[cyan]Launching everyday browser with remote debugging port 9222...[/cyan]")
    if browser.launch_everyday_browser():
        console.print("[bold green]✔ Everyday browser is ready for Jarvis automation![/bold green]")
    else:
        console.print("[bold red]✖ Could not find or launch everyday browser.[/bold red]")

@app.command()
def audit():
    """Inspect recent execution runs and visual audit trails."""
    am = AuditManager()
    runs = am.list_recent_runs(limit=15)
    if not runs:
        console.print("[dim]No recorded runs found.[/dim]")
        return
    table = Table(title="Jarvis Audit Trail (Recent Runs)")
    table.add_column("Run ID", style="cyan")
    table.add_column("Goal", style="white")
    table.add_column("Status", style="green")
    table.add_column("Steps", style="yellow")
    for r in runs:
        st_color = "green" if r.get("status") == "success" else "red"
        table.add_row(
            r.get("run_id", ""),
            r.get("goal", "")[:40] + "...",
            f"[{st_color}]{r.get('status', '').upper()}[/{st_color}]",
            str(len(r.get("steps", []))),
        )
    console.print(table)

# Vault sub-commands
vault_app = typer.Typer(help="Manage secure credentials in Secret Vault")
app.add_typer(vault_app, name="vault")

@vault_app.command("set")
def vault_set(key: str = typer.Argument(..., help="Secret name (e.g. telegram_bot_token)"),
              value: str = typer.Argument(..., help="Secret value")):
    """Store a secret in the vault."""
    vault = SecretVault()
    if vault.set_secret(key, value):
        console.print(f"[green]✔ Secret '{key}' saved successfully.[/green]")
    else:
        console.print(f"[red]✖ Failed to save secret '{key}'.[/red]")

@vault_app.command("get")
def vault_get(key: str = typer.Argument(..., help="Secret name")):
    """Retrieve a secret."""
    vault = SecretVault()
    val = vault.get_secret(key)
    if val:
        masked = val[:3] + "..." + val[-3:] if len(val) > 8 else "***"
        console.print(f"[cyan]{key}:[/cyan] {masked}")
    else:
        console.print(f"[yellow]Secret '{key}' not found.[/yellow]")

@vault_app.command("list")
def vault_list():
    """List stored secret keys."""
    vault = SecretVault()
    keys = vault.list_keys()
    if not keys:
        console.print("[dim]No secrets currently stored in fallback vault.[/dim]")
        return
    table = Table(title="Stored Credentials in Vault")
    table.add_column("Key Name", style="cyan")
    for k in keys:
        table.add_row(k)
    console.print(table)

# Config sub-commands
config_app = typer.Typer(help="Inspect and update Jarvis configuration")
app.add_typer(config_app, name="config")

@config_app.command("show")
def config_show():
    """Display current configuration."""
    cfg = load_config()
    import yaml
    console.print(Panel(yaml.dump(cfg.model_dump()), title="Current Jarvis Configuration", border_style="cyan"))

@config_app.command("set")
def config_set(key: str = typer.Argument(..., help="Config dot-path (e.g. model.policy, autonomous_mode)"),
               value: str = typer.Argument(..., help="Value to set")):
    """Set a configuration value."""
    cfg = load_config()
    data = cfg.model_dump()
    parts = key.split(".")
    target = data
    for p in parts[:-1]:
        if p not in target:
            target[p] = {}
        target = target[p]

    val: any = value
    if value.lower() == "true":
        val = True
    elif value.lower() == "false":
        val = False

    target[parts[-1]] = val
    new_cfg = JarvisConfig(**data)
    save_config(new_cfg)
    console.print(f"[green]✔ Config updated: {key} = {val}[/green]")

# Memory sub-commands
memory_app = typer.Typer(help="Manage lean Markdown memory")
app.add_typer(memory_app, name="memory")

@memory_app.command("list")
def memory_list():
    """List all memory topics and workflow files."""
    cfg = load_config()
    from jarvis.memory.store import MemoryStore
    store = MemoryStore(cfg.memory)
    console.print(f"[cyan]Memory Directory:[/cyan] {store.memory_dir}")
    files = list(store.memory_dir.glob("**/*.md"))
    table = Table(title="Structured Memory Files")
    table.add_column("Topic / File", style="green")
    table.add_column("Lines", style="yellow")
    for f in sorted(files):
        rel = f.relative_to(store.memory_dir)
        lines = len(f.read_text(encoding="utf-8").splitlines())
        table.add_row(str(rel), str(lines))
    console.print(table)

def main():
    app()

if __name__ == "__main__":
    main()
