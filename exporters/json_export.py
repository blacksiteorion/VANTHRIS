import json
import os

def export_full_report(manifest, analysis, out_path):
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump({"manifest": manifest, "analysis": analysis}, f, indent=2, ensure_ascii=False)
    return out_path
