import csv
import os

def export_artifacts_csv(artifacts, out_path):
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    fields = ["source_path", "size_bytes", "category", "sha256", "acquired_at"]
    with open(out_path, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        for a in artifacts:
            w.writerow(a)
    return out_path
