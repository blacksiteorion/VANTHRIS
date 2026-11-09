from utils.logger import log


def analyze_recovery(db_result, media_records, orphans):
    """
    Produce recovery findings with confidence classification.
    Never fabricates records. Only reports what the data supports.
    """
    findings = []

    # 1. Freelist hint
    fl = db_result.get("freelist_count")
    if fl is not None and fl > 0:
        findings.append({
            "type": "freelist_pages",
            "confidence": "Potentially Recoverable",
            "description": (
                f"Database contains {fl} freelist page(s). These may contain remnants "
                "of deleted records. No data was extracted; this is a forensic hint only."
            ),
            "source": db_result.get("database_path"),
        })
    elif db_result.get("analyzed"):
        findings.append({
            "type": "freelist_pages",
            "confidence": "Confirmed",
            "description": "No freelist pages detected. Deleted records are unlikely to be present in this copy.",
            "source": db_result.get("database_path"),
        })

    # 2. Missing DB (honest limitation)
    if not db_result.get("analyzed"):
        findings.append({
            "type": "missing_database",
            "confidence": "Confirmed",
            "description": (
                "No WhatsApp database was available for analysis. "
                "Deleted-message recovery cannot be performed without the original database."
            ),
            "source": None,
        })

    # 3. Orphaned media
    if orphans:
        findings.append({
            "type": "orphaned_media",
            "confidence": "Unverified",
            "description": (
                f"{len(orphans)} media file(s) exist on disk but could not be matched to any "
                "chat record in the analyzed database. These may be orphaned, or the database "
                "may not contain the referencing message. Manual review recommended."
            ),
            "source": "media_scan",
            "count": len(orphans),
        })

    # 4. If DB exists but no orphans
    if db_result.get("analyzed") and not orphans and media_records:
        findings.append({
            "type": "orphaned_media",
            "confidence": "Confirmed",
            "description": "All acquired media matched at least one chat reference.",
            "source": "media_scan",
            "count": 0,
        })

    log.info(f"[green]✔ Recovery findings:[/] {len(findings)}")
    return findings
