import sys
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from utils.logger import log
from core.device import check_adb_installed, get_connected_devices, get_device_info

console = Console()

def print_banner():
    """Prints the VANTHRIS CLI banner."""
    banner = """
[bold green]VANTHRIS[/bold green]
[white]Android Digital Forensics[/white]

[dim italic]Recover the evidence. Preserve the truth.[/dim italic]
    """
    console.print(Panel(banner, border_style="green", expand=False))

def main():
    print_banner()

    # 1. Environment Check
    log.info("[cyan]Checking environment...[/cyan]")
    if not check_adb_installed():
        log.error("[bold red]ADB is not installed or not in system PATH.[/bold red]")
        log.info("Please install Android Platform Tools and ensure 'adb' is accessible.")
        sys.exit(1)
    log.info("[green]✔ ADB detected.[/green]")

    # 2. Device Detection
    log.info("[cyan]Scanning for connected devices...[/cyan]")
    devices = get_connected_devices()

    if not devices:
        log.warning("[bold yellow]No devices found.[/bold yellow]")
        log.info("Please connect an Android device via USB, enable USB Debugging, and authorize the computer.")
        sys.exit(1)

    if len(devices) > 1:
        log.warning(f"Multiple devices detected. Using the first one: {devices[0]}")
        serial = devices[0]
    else:
        serial = devices[0]
        log.info("[green]✔ Device connected.[/green]")

    # 3. Information Gathering
    log.info("[cyan]Extracting device information...[/cyan]")
    info = get_device_info(serial)

    # 4. Display Info
    table = Table(title="Device Overview", title_style="bold green")
    table.add_column("Property", style="cyan")
    table.add_column("Value", style="white")

    table.add_row("Serial", info["serial"])
    table.add_row("Manufacturer", info["manufacturer"])
    table.add_row("Model", info["model"])
    table.add_row("Android Version", info["android_version"])
    
    if info["whatsapp_installed"]:
        table.add_row("WhatsApp", "[green]Installed[/green]")
    else:
        table.add_row("WhatsApp", "[red]Not Detected[/red]")

    console.print(table)

    # Next steps
    console.print("\n[bold cyan]Ready for authorized acquisition.[/bold cyan]")
    console.print("[dim](Acquisition module coming in Phase 3)[/dim]")

if __name__ == "__main__":
    main()