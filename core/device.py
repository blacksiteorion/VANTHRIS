import subprocess
from utils.logger import log

def check_adb_installed():
    """Check if ADB is installed and accessible in the system PATH."""
    try:
        subprocess.run(["adb", "version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

def get_connected_devices():
    """Returns a list of connected device serial numbers."""
    try:
        result = subprocess.run(["adb", "devices"], capture_output=True, text=True, check=True)
        lines = result.stdout.strip().split('\n')[1:]
        devices = [line.split('\t')[0] for line in lines if '\tdevice' in line]
        return devices
    except Exception as e:
        log.error(f"[bold red]Error reading ADB devices:[/] {e}")
        return []

def get_device_info(serial):
    """Fetches manufacturer, model, and Android version from the device."""
    info = {
        "serial": serial,
        "manufacturer": "Unknown",
        "model": "Unknown",
        "android_version": "Unknown",
        "whatsapp_installed": False
    }

    try:
        info["manufacturer"] = subprocess.run(["adb", "-s", serial, "shell", "getprop", "ro.product.manufacturer"], capture_output=True, text=True).stdout.strip().capitalize()
        info["model"] = subprocess.run(["adb", "-s", serial, "shell", "getprop", "ro.product.model"], capture_output=True, text=True).stdout.strip()
        info["android_version"] = subprocess.run(["adb", "-s", serial, "shell", "getprop", "ro.build.version.release"], capture_output=True, text=True).stdout.strip()

        wa_check = subprocess.run(["adb", "-s", serial, "shell", "pm", "list", "packages", "com.whatsapp"], capture_output=True, text=True).stdout
        if "package:com.whatsapp" in wa_check:
            info["whatsapp_installed"] = True

    except Exception as e:
        log.error(f"[bold red]Failed to get device info:[/] {e}")

    return info
