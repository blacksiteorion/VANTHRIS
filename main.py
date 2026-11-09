import sys
import os
import argparse

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Confirm

from utils.logger import log
from core.device import check_adb_installed, get_connected_devices, get_device_info
from core.acquisition import run_acquisition
from core.analysis import run_analysis

console = Console()


def print_banner():
    banner = """
[bold green]VANTHRIS[/bold green]
[white]Android Digital Forensics[/white]

[dim italic]Recover the evidence. Preserve the truth.[/dim italic]
    """
    console.print(Panel(banner, border_style="green", expand=False))


def parse_args():
    p = argparse.ArgumentParser(description="VANTHRIS — Android Digital Forensics")
    p.add_argument("--db", help="Path to an acquired WhatsApp database (msgstore.db) for analysis")
    p.add_argument("--evidence", help="Path to an existing evidence directory to analyze (skips ADB)")
    return p.parse_args()


def main():
    args = parse_args()
    print_banner()

    # Direct analysis mode
    if args.evidence:
        log.info(f"[cyan]Analyzing existing evidence directory:[/] {args.evidence}")
        run_analysis(args.evidence, args.db)
        console.print("[green]Analysis complete.[/green]")
        return

    # Live acquisition mode
    log.info("[cyan]Checking environment...[/cyan]")
    if not check_adb_installed():
        log.error("[bold red]ADB is not installed or not in system PATH.[/bold red]")
        sys.exit(1)
    log.info("[green]✔ ADB detected.[/green]")

    devices = get_connected_devices()
    if not devices:
        log.warning("[bold yellow]No devices found.[/bold yellow]")
        sys.exit(1)

    serial = devices[0]
    log.info(f"[green]✔ Device connected:[/] {serial}")

    info = get_device_info(serial)
    table = Table(title="Device Overview", title_style="bold green")
    table.add_column("Property", style="cyan")
    table.add_column("Value", style="white")
    for k in ("serial", "manufacturer", "model", "android_version"):
        table.add_row(k.replace("_", " ").title(), str(info.get(k)))
    table.add_row(
        "WhatsApp",
        "[green]Installed[/green]" if info["whatsapp_installed"] else "[red]Not Detected[/red]",
    )
    console.print(table)

    console.print()
    console.print(Panel(
        "[bold yellow]Authorization Required[/bold yellow]\n\n"
        "Proceeding confirms you own this device or have explicit permission to examine it.",
        border_style="yellow", title="Consent",
    ))
    if not Confirm.ask("[bold]Proceed with authorized acquisition?[/bold]", default=False):
        log.info("Cancelled.")
        sys.exit(0)

    manifest_path = run_acquisition(serial, info)
    evidence_dir = os.path.dirname(manifest_path)

    console.print()
    log.info("[cyan]Running analysis...[/cyan]")
    run_analysis(evidence_dir, args.db)

    console.print(Panel(
        f"[green]Acquisition and analysis complete.[/green]\n\n"
        f"Manifest:  [cyan]{manifest_path}[/cyan]\n"
        f"Analysis:  [cyan]{os.path.join(evidence_dir, 'analysis.json')}[/cyan]\n\n"
        f"Review these files to see hashes, parsed chats, media inventory, and recovery findings.",
        border_style="green", title="Phase 4 Complete",
    ))
    console.print("[dim](Dashboard generation coming in Phase 5)[/dim]")


if __name__ == "__main__":
    main()
