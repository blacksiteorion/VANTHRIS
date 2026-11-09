import os
import tempfile
import unittest

from tests.fixtures import (
    make_synthetic_whatsapp_db,
    make_synthetic_media_tree,
    make_synthetic_manifest,
)
from core.analysis import run_analysis
from dashboard.generator import generate_dashboard


class TestDashboardGeneration(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.evidence = os.path.join(self.tmp, "evidence", "Synthetic_TestModel")
        os.makedirs(self.evidence, exist_ok=True)
        make_synthetic_media_tree(os.path.join(self.evidence, "media"))
        make_synthetic_manifest(self.evidence, model="TestModel")
        self.db_path = make_synthetic_whatsapp_db(os.path.join(self.tmp, "msgstore.db"))
        run_analysis(self.evidence, self.db_path)

    def test_html_file_is_generated(self):
        html = generate_dashboard(self.evidence)
        self.assertIsNotNone(html)
        self.assertTrue(os.path.exists(html))
        self.assertTrue(html.endswith("Synthetic_TestModel.html"))

    def test_html_contains_required_sections(self):
        html = generate_dashboard(self.evidence)
        with open(html, encoding="utf-8") as f:
            content = f.read()
        for marker in [
            "VANTHRIS EVIDENCE CONSOLE",
            'id="tab-overview"',
            'id="tab-chats"',
            'id="tab-media"',
            'id="tab-recovered"',
            'id="tab-forensic"',
            'id="tab-export"',
        ]:
            self.assertIn(marker, content, f"Missing: {marker}")

    def test_no_external_resources(self):
        html = generate_dashboard(self.evidence)
        with open(html, encoding="utf-8") as f:
            content = f.read()
        self.assertNotIn("http://", content)
        self.assertNotIn("https://", content)
        self.assertNotIn("cdn.", content.lower())
        self.assertNotIn("<link ", content.lower())

    def test_renders_synthetic_chat_text(self):
        html = generate_dashboard(self.evidence)
        with open(html, encoding="utf-8") as f:
            content = f.read()
        self.assertIn("synthetic message #1", content)

    def test_renders_recovery_findings(self):
        html = generate_dashboard(self.evidence)
        with open(html, encoding="utf-8") as f:
            content = f.read()
        self.assertIn("ORPHANED_MEDIA", content.upper())

    def test_exports_created(self):
        generate_dashboard(self.evidence)
        exports = os.path.join(self.evidence, "exports")
        for name in ("chats.txt", "summary.csv", "report.json", "evidence.zip"):
            self.assertTrue(os.path.exists(os.path.join(exports, name)), name)


if __name__ == "__main__":
    unittest.main()
