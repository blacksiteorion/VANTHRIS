import os
import json
from datetime import datetime, timezone

from utils.logger import log
from modules.whatsapp.database import analyze_database
from modules.whatsapp.media import discover_media, find_orphans
from core.recovery import analyze_recovery


def run_analysis(evidence_dir, db_path=None):
    """
    Full Phase 4 pipeline:
      1. Analyze DB if available.
      2. Discover media in evidence_dir/media.
      3. Detect orphans.
      4. Classify recovery findings.
      5. Write analysis.json.
    """
    if not os.path.isdir(evidence_dir):
        log.error(f"[bold red]Evidence directory not found:[/] {evidence_dir}")
        return None

    workdir = os.path.join(evidence_dir, "_work")
    os.makedirs(workdir, exist_ok=True)

    limitations = []
    media_root = os.path.join(evidence_dir, "media")

    # 1. Database
    db_result, db_limits = analyze_database(db_path, workdir)
    limitations.extend(db_limits)

    # 2. Media
    media_records = discover_media(media_root)
    if not media_records:
        limitations.append("No media files were found in the evidence directory.")

    # 3. Orphans
    orphans = find_orphans(media_records, db_result.get("messages", []))

    # 4. Recovery
    recovery_findings = analyze_recovery(db_result, media_records, orphans)

    # 5. Assemble
    analysis = {
        "tool": "VANTHRIS",
        "phase": 4,
        "analysis_utc": datetime.now(timezone.utc).isoformat(),
        "database": {
            "analyzed": db_result.get("analyzed"),
            "integrity_ok": db_result.get("integrity_ok"),
            "message_count": db_result.get("message_count"),
            "freelist_count": db_result.get("freelist_count"),
            "tables": list(db_result.get("tables", {}).keys()),
        },
        "messages": db_result.get("messages", []),
        "media": media_records,
        "orphaned_media": orphans,
        "recovery_findings": recovery_findings,
        "limitations": limitations,
    }

    out_path = os.path.join(evidence_dir, "analysis.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(analysis, f, indent=2, ensure_ascii=False)

    log.info(f"[green]✔ Analysis written:[/] {out_path}")
    return out_path
