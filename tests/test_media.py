import os
import tempfile
import unittest

from tests.fixtures import make_synthetic_whatsapp_db, make_synthetic_media_tree
from modules.whatsapp.database import analyze_database
from modules.whatsapp.media import discover_media, find_orphans


class TestMediaDiscovery(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.media_root = make_synthetic_media_tree(os.path.join(self.tmp, "media"))
        self.db = make_synthetic_whatsapp_db(os.path.join(self.tmp, "msgstore.db"))

    def test_discovers_all_files(self):
        self.assertEqual(len(discover_media(self.media_root)), 4)

    def test_classifies_types(self):
        by_name = {r["filename"]: r for r in discover_media(self.media_root)}
        self.assertEqual(by_name["IMG-20231114-WA0001.jpg"]["type"], "image")
        self.assertEqual(by_name["VID-20231114-WA0002.mp4"]["type"], "video")
        self.assertEqual(by_name["PTT-20231120-WA8888.opus"]["type"], "audio")

    def test_hashes_are_populated(self):
        for r in discover_media(self.media_root):
            self.assertEqual(len(r["sha256"]), 64)

    def test_orphan_detection(self):
        recs = discover_media(self.media_root)
        db_result, _ = analyze_database(self.db, os.path.join(self.tmp, "work"))
        orphans = {o["filename"] for o in find_orphans(recs, db_result["messages"])}
        self.assertNotIn("IMG-20231114-WA0001.jpg", orphans)
        self.assertNotIn("VID-20231114-WA0002.mp4", orphans)
        self.assertIn("IMG-20231120-WA9999.jpg", orphans)
        self.assertIn("PTT-20231120-WA8888.opus", orphans)

    def test_no_db_returns_no_orphans(self):
        self.assertEqual(find_orphans(discover_media(self.media_root), []), [])


if __name__ == "__main__":
    unittest.main()
