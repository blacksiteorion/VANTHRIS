import os

def export_chats_txt(messages, out_path):
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("VANTHRIS CHAT EXPORT\n")
        f.write("=" * 60 + "\n\n")
        for m in messages:
            direction = "OUT" if m.get("from_me") else "IN "
            ts = m.get("timestamp_iso") or "unknown-time"
            sender = m.get("sender") or m.get("jid") or "unknown"
            text = m.get("text") or ""
            f.write(f"[{ts}] [{direction}] {sender}:\n    {text}\n\n")
    return out_path
