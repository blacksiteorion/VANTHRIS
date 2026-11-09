import os
import sqlite3
import hashlib
import json
from datetime import datetime, timezone


def make_synthetic_whatsapp_db(path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    if os.path.exists(path):
        os.remove(path)
    conn = sqlite3.connect(path)
    conn.execute("""
        CREATE TABLE message (
            _id INTEGER PRIMARY KEY,
            key_remote_jid TEXT,
            remote_resource TEXT,
            data TEXT,
            timestamp INTEGER,
            from_me INTEGER
        )
    """)
    rows = [
        (1, "alice@s.whatsapp.net", None, "Hello, this is a synthetic message #1", 1700000000000, 0),
        (2, "alice@s.whatsapp.net", None, "Synthetic reply #2", 1700000060000, 1),
        (3, "bob@s.whatsapp.net",   None, "IMG-20231114-WA0001.jpg attached", 1700000120000, 0),
        (4, "bob@s.whatsapp.net",   None, "Untracked file: VID-20231114-WA0002.mp4", 1700000180000, 0),
        (5, "carol@s.whatsapp.net", None, "Last synthetic record", 1700000240000, 1),
    ]
    conn.executemany(
        "INSERT INTO message (_id, key_remote_jid, remote_resource, data, timestamp, from_me) VALUES (?,?,?,?,?,?)",
        rows,
    )
    conn.commit()
    conn.close()
    return path


def make_synthetic_media_tree(root):
    os.makedirs(root, exist_ok=True)
    files = [
        ("Images/IMG-20231114-WA0001.jpg", b"\xff\xd8\xff\xe0synthetic-jpeg-1"),
        ("Video/VID-20231114-WA0002.mp4",  b"\x00\x00\x00\x18synthetic-mp4-2"),
        ("Images/IMG-20231120-WA9999.jpg", b"\xff\xd8\xff\xe0synthetic-jpeg-orphan"),
        ("Audio/PTT-20231120-WA8888.opus", b"OggSsynthetic-opus-orphan"),
    ]
    for rel, payload in files:
        full = os.path.join(root, rel)
        os.makedirs(os.path.dirname(full), exist_ok=True)
        with open(full, "wb") as f:
            f.write(payload)
    return root


def make_synthetic_manifest(evidence_dir, device_name="Test_Device", model="TestModel"):
    artifacts = []
    media_root = os.path.join(evidence_dir, "media")
    for root, _, files in os.walk(media_root):
        for fname in files:
            full = os.path.join(root, fname)
            with open(full, "rb") as f:
                sha = hashlib.sha256(f.read()).hexdigest()
            artifacts.append({
                "source_path": "/sdcard/Android/media/com.whatsapp/WhatsApp/Media/" +
                               os.path.relpath(full, media_root).replace(os.sep, "/"),
                "local_path": full,
                "size_bytes": os.path.getsize(full),
                "sha256": sha,
                "acquired_at": datetime.now(timezone.utc).isoformat(),
                "category": "media",
            })
    manifest = {
        "tool": "VANTHRIS",
        "acquisition_utc": datetime.now(timezone.utc).isoformat(),
        "device": {
            "serial": "SYNTHETIC0001",
            "manufacturer": "Synthetic",
            "model": model,
            "android_version": "14",
            "whatsapp_installed": True,
        },
        "artifacts": artifacts,
        "total_artifacts": len(artifacts),
        "limitations": [
            "SYNTHETIC TEST DATA — not from a real device.",
            "WhatsApp database not acquired in this synthetic fixture.",
        ],
    }
    path = os.path.join(evidence_dir, "manifest.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
    return path
