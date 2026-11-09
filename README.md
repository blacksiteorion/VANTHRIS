# VANTHRIS

**Android Digital Forensics — Recover the evidence. Preserve the truth.**

VANTHRIS is an open-source Android forensic acquisition and analysis toolkit focused on **authorized** WhatsApp-related artifacts. It is built for cybersecurity students, digital forensics learners, security researchers, and authorized forensic examinations.

> **Responsible use.** VANTHRIS is designed exclusively for examinations of devices you own or have explicit, documented permission to examine. It does not bypass Android security, encryption, or application sandboxing, and it does not upload any acquired data to any server.

---

## What VANTHRIS does

1. Detects connected Android devices via ADB.
2. Runs a consent gate before touching any file.
3. Acquires accessible WhatsApp media from shared storage.
4. Computes SHA-256 for every acquired artifact.
5. Parses an acquired WhatsApp SQLite database (if provided).
6. Classifies recovery findings with honest confidence labels.
7. Generates a standalone, offline HTML forensic dashboard named after the device.

## What VANTHRIS does not do

- It does not access `/data/data/com.whatsapp/` on a non-rooted device. That directory is protected by Android's application sandbox.
- It does not bypass authentication, encryption, or end-to-end encryption.
- It does not fabricate recovered data. If a finding cannot be verified, it is labeled Unverified or Potentially Recoverable.
- It does not transmit evidence, telemetry, or usage data anywhere.

---

## Installation

### Requirements
- Linux (Ubuntu/Debian tested) or macOS
- Python 3.10+
- Android Platform Tools (adb in PATH)
- An Android device with USB debugging enabled

### Setup

    git clone https://github.com/blacksiteorion/VANTHRIS.git
    cd VANTHRIS
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt

### Android prerequisites
1. Enable Developer Options on the device.
2. Enable USB Debugging.
3. Connect the device via USB and authorize this computer when prompted.

---

## Usage

### Full pipeline (live device)

    python main.py

Prompts for consent, acquires media, runs analysis, and generates the dashboard.

### Analyze an existing evidence directory

    python main.py --evidence evidence/Samsung_Galaxy_A54 --db /path/to/msgstore.db

### Regenerate only the dashboard

    python main.py --evidence evidence/Samsung_Galaxy_A54 --report-only

The dashboard is written to the evidence directory as `<Manufacturer>_<Model>.html`.

---

## Output structure

    evidence/<Manufacturer>_<Model>/
    |-- manifest.json
    |-- analysis.json
    |-- media/
    |-- exports/
    |   |-- chats.txt
    |   |-- summary.csv
    |   |-- report.json
    |   `-- evidence.zip
    |-- _work/
    `-- <Manufacturer>_<Model>.html

---

## Limitations (honest disclosure)

| Limitation | Reason |
|---|---|
| WhatsApp database not acquired on non-rooted devices | Android app sandbox |
| Encrypted .crypt14 backups not decrypted | Would require bypassing WhatsApp's protection |
| Deleted-message recovery is best-effort | Depends on freelist remnants, WAL state, and device wear |
| Media-orphan detection is heuristic | Based on filename-to-message-text matching |

Every limitation is also written into the manifest at acquisition time.

---

## Testing

Tests use only synthetic fixtures. No real WhatsApp data is ever included.

    python -m tests.run_all

Coverage:
- SHA-256 integrity (empty, small, multi-chunk)
- SQLite parsing on a synthetic WhatsApp-schema database
- Media discovery, type classification, orphan detection
- Dashboard generation (file name, required sections, no external URLs)
- TXT / CSV / JSON / ZIP exporters

---

## Project layout

    VANTHRIS/
    |-- main.py
    |-- requirements.txt
    |-- README.md
    |-- SECURITY.md
    |-- LICENSE
    |-- .gitignore
    |-- core/
    |   |-- device.py
    |   |-- acquisition.py
    |   |-- integrity.py
    |   |-- analysis.py
    |   `-- recovery.py
    |-- modules/whatsapp/
    |   |-- database.py
    |   `-- media.py
    |-- dashboard/
    |   |-- generator.py
    |   `-- templates/index.html
    |-- exporters/
    |   |-- txt.py
    |   |-- csv.py
    |   |-- json_export.py
    |   `-- zip_export.py
    |-- utils/logger.py
    `-- tests/

---

## Security policy

See [SECURITY.md](SECURITY.md) for vulnerability reporting and responsible-use guidance.

## License

See [LICENSE](LICENSE).
