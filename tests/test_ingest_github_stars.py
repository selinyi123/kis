"""KIS-018 GitHub Stars ingest tests."""

import os
import shutil
import sys
import tempfile
import unittest

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(_ROOT, "src"))

from kis.ingest import runner  # noqa: E402
from kis.store import Store  # noqa: E402

_FIX = os.path.join(_ROOT, "tests", "fixtures", "github_stars.json")


class TestIngestGithubStars(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
        self.db = os.path.join(self.tmp, "k.db")

    def test_import_counts(self):
        store = Store(self.db)
        rep = runner.ingest("github-stars", _FIX, store, os.path.join(self.tmp, "v"))
        self.assertEqual(rep.total_seen, 4)
        self.assertEqual(rep.created, 2)
        self.assertEqual(rep.skipped_duplicate, 1)
        self.assertEqual(rep.blocked, 1)          # leak/repo with token=ghp_...
        self.assertEqual(rep.errors, 0)
        self.assertEqual(Store(self.db).count("github_star"), 2)

    def test_created_cards_default_inbox_pending(self):
        store = Store(self.db)
        runner.ingest("github-stars", _FIX, store, None)
        for c in Store(self.db).all_cards():
            self.assertEqual(c["lifecycle"]["state"], "inbox")
            self.assertNotIn("review", c)  # pending


if __name__ == "__main__":
    unittest.main()
