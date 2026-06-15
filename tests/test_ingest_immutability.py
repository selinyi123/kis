"""KIS-018 immutability: inbox-only, no auto reviewed/canonical, no overwrite."""

import os
import shutil
import sys
import tempfile
import unittest

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(_ROOT, "src"))

from kis.card import github_star_card  # noqa: E402
from kis.ingest import runner  # noqa: E402
from kis.store import Store  # noqa: E402

_FIX = os.path.join(_ROOT, "tests", "fixtures", "github_stars.json")


class TestIngestImmutability(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
        self.db = os.path.join(self.tmp, "k.db")

    def test_no_auto_reviewed_or_canonical(self):
        runner.ingest("github-stars", _FIX, Store(self.db), None)
        states = {c["lifecycle"]["state"] for c in Store(self.db).all_cards()}
        self.assertEqual(states, {"inbox"})
        self.assertNotIn("canonical", states)
        self.assertNotIn("reviewed", states)

    def test_does_not_modify_existing_canonical(self):
        store = Store(self.db)
        # Pre-seed a canonical card for MemOS (same id GBrain ingest will produce)
        memos = github_star_card({"full_name": "MemTensor/MemOS", "html_url": "https://github.com/MemTensor/MemOS",
                                  "description": "Self-evolving memory OS for agents", "language": "TypeScript",
                                  "stargazers_count": 9852, "topics": ["memory", "rag"]})
        memos["lifecycle"]["state"] = "canonical"
        memos["lifecycle"]["version"] = 3
        store.upsert(memos)
        # Ingest the fixture (contains the same MemOS) -> must be a duplicate, untouched
        rep = runner.ingest("github-stars", _FIX, Store(self.db), None)
        after = Store(self.db).get(memos["id"])
        self.assertEqual(after["lifecycle"]["state"], "canonical")  # not downgraded to inbox
        self.assertGreaterEqual(rep.skipped_duplicate, 1)


if __name__ == "__main__":
    unittest.main()
