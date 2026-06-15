"""KIS-018 browser bookmark ingest tests."""

import os
import shutil
import sys
import tempfile
import unittest

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(_ROOT, "src"))

from kis.ingest import runner  # noqa: E402
from kis.store import Store  # noqa: E402

_FIX = os.path.join(_ROOT, "tests", "fixtures", "bookmarks.html")


class TestIngestBookmarks(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
        self.db = os.path.join(self.tmp, "k.db")

    def test_import_counts(self):
        store = Store(self.db)
        rep = runner.ingest("bookmarks", _FIX, store, os.path.join(self.tmp, "v"))
        self.assertEqual(rep.total_seen, 5)
        self.assertEqual(rep.created, 3)            # chatgpt, huggingface, github
        self.assertEqual(rep.skipped_duplicate, 1)  # chatgpt dup
        self.assertEqual(rep.blocked, 1)            # 机场 (sensitivity blocked)
        self.assertEqual(Store(self.db).count("web_bookmark"), 3)

    def test_blocked_airport_not_stored(self):
        store = Store(self.db)
        runner.ingest("bookmarks", _FIX, store, None)
        urls = [c["source"]["url"] for c in Store(self.db).all_cards()]
        self.assertFalse(any("pqjc" in u for u in urls))


if __name__ == "__main__":
    unittest.main()
