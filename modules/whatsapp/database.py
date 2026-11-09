import os
import shutil
import sqlite3
from datetime import datetime, timezone
from utils.logger import log


def _copy_db_for_analysis(db_path, workdir):
    """
    Copy the DB and any sidecar WAL/SHM files to a working directory.
    We never analyze the original file directly — forensic principle.
    """
    os.makedirs(workdir, exist_ok=True)
    base = os.path.basename(db_path)
    work_db = os.path.join(workdir, base)

    shutil.copy2(db_path, work_db)
    for ext in ("-wal", "-shm"):
        side = db_path + ext
        if os.path.exists(side):
            shutil.copy2(side, work_db + ext)

    return work_db


def _classify_tables(conn):
    """Return a dict of table_name -> column list."""
    tables = {}
    cur = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
    )
    for (name,) in cur.fetchall():
        cols = []
        try:
            pragma = conn.execute(f"PRAGMA table_info({name})").fetchall()
            cols = [row[1] for row in pragma]
        except sqlite3.DatabaseError:
            pass
        tables[name] = cols
    return tables


def _try_extract_messages(conn, tables):
    """
    WhatsApp DBs vary by version. Try to find a message table
    and pull the most stable columns.
    """
    candidates = ["message", "messages", "message_view"]
    msg_table = next((t for t in candidates if t in tables), None)
    if not msg_table:
        return [], f"No recognizable message table found (checked: {', '.join(candidates)})."

    cols = tables[msg_table]
    # WhatsApp historically uses: _id, key_remote_jid, remote_resource, data, timestamp, from_me, text_data
    wanted = {
        "id": "_id",
        "jid": "key_remote_jid",
        "sender": "remote_resource",
        "text": "data",
        "timestamp": "timestamp",
        "from_me": "from_me",
    }
    selected = {alias: col for alias, col in wanted.items() if col in cols}
    if "timestamp" not in selected:
        return [], f"Message table '{msg_table}' found but no timestamp column."

    col_list = ", ".join(selected.values())
    try:
        rows = conn.execute(f"SELECT {col_list} FROM {msg_table} ORDER BY {selected['timestamp']} ASC").fetchall()
    except sqlite3.DatabaseError as e:
        return [], f"Query failed on '{msg_table}': {e}"

    aliases = list(selected.keys())
    messages = []
    for row in rows:
        rec = dict(zip(aliases, row))
        ts = rec.get("timestamp")
        iso = None
        if isinstance(ts, (int, float)):
            try:
                iso = datetime.fromtimestamp(ts / 1000.0, tz=timezone.utc).isoformat()
            except (OverflowError, OSError, ValueError):
                iso = None
        messages.append({
            "jid": rec.get("jid"),
            "sender": rec.get("sender"),
            "text": rec.get("text"),
            "timestamp_ms": ts,
            "timestamp_iso": iso,
            "from_me": bool(rec.get("from_me") or 0),
        })

    return messages, None


def analyze_database(db_path, workdir):
    """
    Analyze a WhatsApp SQLite database.
    Returns (analysis_dict, limitations_list).
    """
    result = {
        "database_path": db_path,
        "analyzed": False,
        "integrity_ok": None,
        "tables": {},
        "message_count": 0,
        "messages": [],
        "freelist_count": None,
        "error": None,
    }
    limitations = []

    if not db_path or not os.path.exists(db_path):
        limitations.append("No WhatsApp database was provided or found for analysis.")
        return result, limitations

    log.info(f"[cyan]Analyzing database:[/] {db_path}")
    work_db = _copy_db_for_analysis(db_path, workdir)

    try:
        conn = sqlite3.connect(work_db)
    except sqlite3.DatabaseError as e:
        result["error"] = f"Could not open database: {e}"
        limitations.append(result["error"])
        return result, limitations

    try:
        # Integrity
        try:
            integ = conn.execute("PRAGMA integrity_check").fetchone()
            result["integrity_ok"] = (integ and integ[0] == "ok")
        except sqlite3.DatabaseError as e:
            result["integrity_ok"] = False
            limitations.append(f"Integrity check failed: {e}")

        # Freelist (deleted page counter — useful for recovery hints)
        try:
            fl = conn.execute("PRAGMA freelist_count").fetchone()
            result["freelist_count"] = fl[0] if fl else None
        except sqlite3.DatabaseError:
            pass

        # Tables
        tables = _classify_tables(conn)
        result["tables"] = {name: cols for name, cols in tables.items()}

        # Messages
        messages, msg_err = _try_extract_messages(conn, tables)
        result["messages"] = messages
        result["message_count"] = len(messages)
        if msg_err:
            limitations.append(msg_err)
        result["analyzed"] = True

    finally:
        conn.close()

    return result, limitations
