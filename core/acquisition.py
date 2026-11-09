import os
import json
import subprocess
import shutil
from datetime import datetime, timezone

from utils.logger import log
from core.integrity import calculate_sha256


# WhatsApp media paths on Android shared storage.
# These are accessible WITHOUT root on most devices.
WHATSAPP_MEDIA_PATHS = [
    "/sdcard/Android/media/com.whatsapp/WhatsApp/Media/",
    "/sdcard/WhatsApp/Media/",
]

# Directories inside Media/ that may contain artifacts of interest.
MEDIA_SUBDIRS = ["Images", "Video", "Audio", "Documents", "Stickers", "Voice Notes"]


def _sanitize_for_dirname(text):
    """Turn a device model string into a safe directory name."""
    safe = "".join(c if c.isalnum() or c in "_-" else "_" for c in text)
    return safe.strip("_") or "Unknown_Device"


def _run_adb(serial, args, capture=True):
    """Run an ADB command against a specific device."""
    cmd = ["adb", "-s", serial] + args
    try:
        return subprocess.run(cmd, capture_output=capture, text=True, check=True)
    except subprocess.CalledProcessError as e:
        return None


def _device_path_exists(serial, path):
    """Check whether a path exists on the device."""
    result = _run_adb(serial, ["shell", "ls", path])
    return result is not None and result.returncode == 0 and "No such file" not in (result.stdout or "")


def create_evidence_directory(device_info):
    """Create the local evidence directory structure for this device."""
    device_folder = _sanitize_for_dirname(
        f"{device_info.get('manufacturer', 'Unknown')}_{device_info.get('model', 'Unknown')}"
    )
    base = os.path.join("evidence", device_folder)
    media_dir = os.path.join(base, "media")
    os.makedirs(media_dir, exist_ok=True)
    return base, media_dir


def acquire_media(serial, media_dir):
    """
    Pull accessible WhatsApp media directories via ADB.
    Returns a list of acquisition records (one per file).
    """
    records = []
    found_any_source = False

    for device_src in WHATSAPP_MEDIA_PATHS:
        if not _device_path_exists(serial, device_src):
            log.info(f"[dim]  Source not accessible: {device_src}[/dim]")
            continue

        found_any_source = True
        log.info(f"[cyan]  Scanning:[/] {device_src}")

        for subdir in MEDIA_SUBDIRS:
            device_sub = os.path.join(device_src, subdir)
            local_sub = os.path.join(media_dir, subdir)

            if not _device_path_exists(serial, device_sub):
                continue

            log.info(f"    → Pulling {subdir}/")
            os.makedirs(local_sub, exist_ok=True)

            # adb pull
            result = _run_adb(serial, ["pull", device_sub, local_sub])

            # Walk what was pulled and hash every file
            for root, _, files in os.walk(local_sub):
                for fname in files:
                    local_path = os.path.join(root, fname)
                    if not os.path.isfile(local_path):
                        continue
                    rel = os.path.relpath(local_path, media_dir)
                    # Map back to the original device path
                    device_path = device_src.rstrip("/") + "/" + rel.replace(os.sep, "/")

                    sha = calculate_sha256(local_path)
                    records.append({
                        "source_path": device_path,
                        "local_path": local_path,
                        "size_bytes": os.path.getsize(local_path),
                        "sha256": sha,
                        "acquired_at": datetime.now(timezone.utc).isoformat(),
                        "category": "media",
                    })

    if not found_any_source:
        log.warning("[bold yellow]No accessible WhatsApp media directories found.[/bold yellow]")
        log.info("[dim]  This is expected on devices where WhatsApp has never saved media,")
        log.info("  or where shared storage permissions block ADB access.[/dim]")

    return records


def write_manifest(evidence_dir, device_info, records, limitations):
    """Write the forensic manifest.json into the evidence directory."""
    manifest = {
        "tool": "VANTHRIS",
        "acquisition_utc": datetime.now(timezone.utc).isoformat(),
        "device": device_info,
        "artifacts": records,
        "total_artifacts": len(records),
        "limitations": limitations,
    }
    manifest_path = os.path.join(evidence_dir, "manifest.json")
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)
    return manifest_path


def run_acquisition(serial, device_info):
    """
    Orchestrate the full Phase 3 acquisition flow.
    Returns the path to the manifest.json.
    """
    log.info("[cyan]Preparing evidence directory...[/cyan]")
    evidence_dir, media_dir = create_evidence_directory(device_info)
    log.info(f"[green]✔ Evidence directory:[/] {evidence_dir}")

    log.info("[cyan]Acquiring accessible WhatsApp media...[/cyan]")
    records = acquire_media(serial, media_dir)

    limitations = [
        "WhatsApp private database (msgstore.db) not acquired: app sandbox restricts ADB access on non-rooted devices.",
        "The acquisition covers only shared-storage media directories.",
        "No encryption is bypassed. No root exploit is attempted.",
    ]

    log.info(f"[cyan]Hashing and writing manifest ({len(records)} files)...[/cyan]")
    manifest_path = write_manifest(evidence_dir, device_info, records, limitations)

    log.info(f"[green]✔ Acquisition complete.[/green]")
    log.info(f"[green]✔ Manifest written:[/] {manifest_path}")
    return manifest_path
