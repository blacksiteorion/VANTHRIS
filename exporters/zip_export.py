import os
import zipfile

def export_evidence_zip(evidence_dir, out_path):
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    if os.path.exists(out_path):
        os.remove(out_path)
    with zipfile.ZipFile(out_path, "w", zipfile.ZIP_DEFLATED) as z:
        for root, _, files in os.walk(evidence_dir):
            for fname in files:
                full = os.path.join(root, fname)
                # Skip the zip file itself
                if os.path.abspath(full) == os.path.abspath(out_path):
                    continue
                arc = os.path.relpath(full, evidence_dir)
                z.write(full, arc)
    return out_path
