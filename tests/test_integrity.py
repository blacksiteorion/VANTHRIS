import os
import tempfile
import hashlib
import unittest

from core.integrity import calculate_sha256


class TestIntegrity(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.mkdtemp()

    def _write(self, name, content):
        p = os.path.join(self.tmp, name)
        with open(p, "wb") as f:
            f.write(content)
        return p

    def test_empty_file(self):
        p = self._write("empty.bin", b"")
        self.assertEqual(calculate_sha256(p), hashlib.sha256(b"").hexdigest())

    def test_known_payload(self):
        payload = b"VANTHRIS synthetic forensic payload"
        p = self._write("known.bin", payload)
        self.assertEqual(calculate_sha256(p), hashlib.sha256(payload).hexdigest())

    def test_large_file_chunking(self):
        payload = b"A" * (65536 * 3 + 123)
        p = self._write("large.bin", payload)
        self.assertEqual(calculate_sha256(p), hashlib.sha256(payload).hexdigest())

    def test_missing_file_returns_none(self):
        self.assertIsNone(calculate_sha256(os.path.join(self.tmp, "nope.bin")))


if __name__ == "__main__":
    unittest.main()
