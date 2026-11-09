import os
import json
import csv
import tempfile
import unittest

from exporters.txt import export_chats_txt
from exporters.csv import export_artifacts_csv
from exporters.json_export import export_full_report


class TestExporters(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.mkdtemp()

    def test_txt_export(self):
        msgs = [
            {"timestamp_iso": "2023-11-14T22:13:20+00:00", "from_me": False,
             "sender": "alice@s.whatsapp.net", "text": "hi"},
            {"timestamp_iso": "2023-11-14T22:14:20+00:00", "from_me": True,
             "sender": "me", "text": "hello"},
        ]
        out = os.path.join(self.tmp, "chats.txt")
        export_chats_txt(msgs, out)
        with open(out) as f:
            content = f.read()
        self.assertIn("[IN ] alice@s.whatsapp.net:", content)
        self.assertIn("[OUT] me:", content)
        self.assertIn("hi", content)
        self.assertIn("hello", content)

    def test_csv_export(self):
        arts = [{"source_path": "/sdcard/foo.jpg", "size_bytes": 100,
                 "category": "media", "sha256": "a"*64, "acquired_at": "2023-01-01"}]
        out = os.path.join(self.tmp, "summary.csv")
        export_artifacts_csv(arts, out)
        with open(out, newline="") as f:
            rows = list(csv.DictReader(f))
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["source_path"], "/sdcard/foo.jpg")
        self.assertEqual(rows[0]["sha256"], "a"*64)

    def test_json_export(self):
        out = os.path.join(self.tmp, "report.json")
        export_full_report({"tool": "VANTHRIS"}, {"messages": []}, out)
        with open(out) as f:
            data = json.load(f)
        self.assertEqual(data["manifest"]["tool"], "VANTHRIS")
        self.assertIn("analysis", data)


if __name__ == "__main__":
    unittest.main()
