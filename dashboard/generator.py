import os
import json
from datetime import datetime, timezone

from jinja2 import Environment, FileSystemLoader
from utils.logger import log
from exporters.txt import export_chats_txt
from exporters.csv import export_artifacts_csv
from exporters.json_export import export_full_report
from exporters.zip_export import export_evidence_zip


def _safe_device_name(device):
    raw = f"{device.get('manufacturer', 'Unknown')}_{device.get('model', 'Unknown')}"
    return "".join(c if c.isalnum() or c in "_-" else "_" for c in raw).strip("_") or "Unknown_Device"


def generate_dashboard(evidence_dir):
    """
    Build the VANTHRIS EVIDENCE CONSOLE from manifest.json + analysis.json.
    Returns the path to the generated HTML file.
    """
    manifest_path = os.path.join(evidence_dir, "manifest.json")
    analysis_path = os.path.join(evidence_dir, "analysis.json")

    if not os.path.exists(manifest_path):
        log.error(f"[bold red]manifest.json not found in {evidence_dir}[/bold red]")
        return None
    if not os.path.exists(analysis_path):
        log.error(f"[bold red]analysis.json not found in {evidence_dir}[/bold red]")
        return None

    with open(manifest_path, encoding="utf-8") as f:
        manifest = json.load(f)
    with open(analysis_path, encoding="utf-8") as f:
        analysis = json.load(f)

    device = manifest.get("device", {})

    # --- Exports (available for download from the dashboard) ---
    exports_dir = os.path.join(evidence_dir, "exports")
    os.makedirs(exports_dir, exist_ok=True)

    messages = analysis.get("messages", [])
    media = analysis.get("media", [])
    artifacts = manifest.get("artifacts", [])
    recovery = analysis.get("recovery_findings", [])

    if messages:
        export_chats_txt(messages, os.path.join(exports_dir, "chats.txt"))
    export_artifacts_csv(artifacts, os.path.join(exports_dir, "summary.csv"))
    export_full_report(manifest, analysis, os.path.join(exports_dir, "report.json"))
    export_evidence_zip(evidence_dir, os.path.join(exports_dir, "evidence.zip"))

    # --- Build the template context ---
    db = analysis.get("database", {})
    context = {
        "device": device,
        "acquisition_utc": manifest.get("acquisition_utc", "Unknown"),
        "generated_utc": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
        "total_artifacts": manifest.get("total_artifacts", len(artifacts)),
        "message_count": len(messages),
        "media_count": len(media),
        "recovery_count": len(recovery),
        "messages": messages,
        "media": media,
        "artifacts": artifacts,
        "recovery_findings": recovery,
        "limitations": analysis.get("limitations", []) + manifest.get("limitations", []),
        "db_analyzed": db.get("analyzed", False),
        "db_integrity": db.get("integrity_ok"),
        "db_freelist": db.get("freelist_count"),
    }

    # --- Render ---
    template_dir = os.path.join(os.path.dirname(__file__), "templates")
    env = Environment(loader=FileSystemLoader(template_dir), autoescape=True)
    template = env.get_template("index.html")
    html = template.render(**context)

    # --- Write device-named HTML in evidence_dir root ---
    device_name = _safe_device_name(device)
    out_path = os.path.join(evidence_dir, f"{device_name}.html")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html)

    log.info(f"[green]✔ Dashboard generated:[/] {out_path}")
    log.info(f"[green]✔ Exports written to:[/] {exports_dir}")
    return out_path
