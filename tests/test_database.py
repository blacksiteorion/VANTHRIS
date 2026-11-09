import os
import sqlite3
import tempfile
import unittest

from tests.fixtures import make_synthetic_whatsapp_db
from modules.whatsapp.database import analyze_database


class TestDatabaseAnalysis(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.db = make_synthetic_whatsapp_db(os.path.join(self.tmp, "msgstore.db"))
        self.work = os.path.join(self.tmp, "work")

    def test_analyzes_synthetic_db(self):
        result, limitations = analyze_database(self.db, self.work)
        self.assertTrue(result["analyzed"])
        self.assertTrue(result["integrity_ok"])
        self.assertEqual(result["message_count"], 5)

    def test_parses_message_fields(self):
        result, _ = analyze_database(self.db, self.work)
        first = result["messages"][0]
        self.assertEqual(first["jid"], "alice@s.whatsapp.net")
        self.assertIn("synthetic message #1", first["text"])
        self.assertFalse(first["from_me"])
        self.assertEqual(first["timestamp_ms"], 1700000000000)

    def test_from_me_flag(self):
        result, _ = analyze_database(self.db, self.work)
        outbound = [m for m in result["messages"] if m["from_me"]]
        self.assertEqual(len(outbound), 2)

    def test_missing_db_reports_limitation(self):
        result, limitations = analyze_database(
            os.path.join(self.tmp, "does_not_exist.db"), self.work
        )
        self.assertFalse(result["analyzed"])
        self.assertTrue(any("No WhatsApp database" in l for l in limitations))

    def test_non_whatsapp_db(self):
        bad = os.path.join(self.tmp, "other.db")
        c = sqlite3.connect(bad)
        c.execute("CREATE TABLE unrelated (x INTEGER)")
        c.commit(); c.close()
        result, limitations = analyze_database(bad, self.work)
        self.assertEqual(result["message_count"], 0)
        self.assertTrue(any("message table" in l.lower() for l in limitations))


if __name__ == "__main__":
    unittest.main()
