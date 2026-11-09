import os
import mimetypes
from utils.logger import log
from core.integrity import calculate_sha256


MEDIA_TYPE_MAP = {
    "Images": "image",
    "Video": "video",
    "Audio": "audio",
    "Voice Notes": "audio",
    "Documents": "document",
    "Stickers": "sticker",
}


def _infer_type(relpath):
    """Infer media type from the acquisition subdirectory."""
    parts = relpath.replace("\\", "/").split("/")
    for p in parts:
        if p in MEDIA_TYPE_MAP:
            return MEDIA_TYPE_MAP[p]
    mime, _ = mimetypes.guess_type(relpath)
    if mime:
        return mime.split("/")[0]
    return "unknown"


def discover_media(media_root):
    """
    Walk an acquired media directory and classify every file.
    Returns a list of media records.
    """
    records = []
    if not media_root or not os.path.isdir(media_root):
        return records

    for root, _, files in os.walk(media_root):
        for fname in files:
            local_path = os.path.join(root, fname)
            rel = os.path.relpath(local_path, media_root)
            try:
                size = os.path.getsize(local_path)
            except OSError:
                size = None
            records.append({
                "local_path": local_path,
                "relative_path": rel,
                "filename": fname,
                "type": _infer_type(rel),
                "mime_guess": mimetypes.guess_type(fname)[0],
                "size_bytes": size,
                "sha256": calculate_sha256(local_path),
            })

    log.info(f"[green]✔ Media discovered:[/] {len(records)} files")
    return records


def find_orphans(media_records, db_messages):
    """
    Orphaned media = files present on disk that are NOT referenced in the DB.
    Requires DB message text; matches on filename tokens.
    Returns a list of orphaned media records.
    """
    if not db_messages:
        # No DB -> we cannot establish orphan status. Mark all as unverified.
        return []

    referenced = set()
    for m in db_messages:
        text = (m.get("text") or "")
        referenced.add(text)

    orphans = []
    for rec in media_records:
        fname = rec["filename"]
        stem = fname.rsplit(".", 1)[0]
        # WhatsApp filenames usually embed "IMG-YYYYMMDD-WA####.jpg"
        # If stem appears anywhere in message text, treat as referenced.
        if not any(stem and stem in t for t in referenced):
            orphans.append(rec)

    return orphans
