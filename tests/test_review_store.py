"""KIS-014 store tests — persistence, optimistic guard, candidate filtering."""

import os
import shutil
import sys
import tempfile
import unittest

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(_ROOT, "src"))

from kis.card import github_star_card  # noqa: E402
from kis.enrich.heuristic import enrich_card  # noqa: E402
from kis.review.actions import apply_review  # noqa: E402
from kis.store import Store  # noqa: E402

_REPO = {"full_name": "x/y", "html_url": "https://github.com/x/y", "description": "memory",
         "language": "Python", "stargazers_count": 1, "topics": ["memory"]}


class TestReviewStore(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
        self.db = os.path.join(self.tmp, "k.db")
        self.s = Store(self.db)
        self.addCleanup(self.s.close)
        self.card = enrich_card(github_star_card(_REPO))
        self.s.upsert(self.card)

    def test_save_review_persists(self):
        out, _ = apply_review(self.s.get_card(self.card["id"]), "reviewed", "ok")
        self.s.save_review(out)
        again = self.s.get_card(self.card["id"])
        self.assertEqual(again["lifecycle"]["state"], "reviewed")
        self.assertEqual(again["review"]["decision"], "reviewed")
        self.assertEqual(again["lifecycle"]["version"], self.card["lifecycle"]["version"] + 1)

    def test_optimistic_lock_conflict(self):
        out, _ = apply_review(self.s.get_card(self.card["id"]), "reviewed", "ok")
        self.s.save_review(out)             # advances on-disk to v2
        with self.assertRaises(RuntimeError):
            self.s.save_review(out)         # stale v2 write again -> conflict

    def test_list_candidates_filter_and_blocked_excluded(self):
        blk = enrich_card(github_star_card({**_REPO, "full_name": "a/b", "html_url": "https://github.com/a/b"}))
        blk["safety"]["sensitivity"] = "blocked"
        self.s.upsert(blk)
        inbox = self.s.list_review_candidates(status="inbox")
        ids = {c["id"] for c in inbox}
        self.assertIn(self.card["id"], ids)
        self.assertNotIn(blk["id"], ids)  # blocked never queued

    def test_full_lifecycle_persisted(self):
        cid = self.card["id"]
        r1, _ = apply_review(self.s.get_card(cid), "reviewed", "verified"); self.s.save_review(r1)
        r2, _ = apply_review(self.s.get_card(cid), "approve_canonical", "promote"); self.s.save_review(r2)
        self.assertEqual(self.s.get_card(cid)["lifecycle"]["state"], "canonical")


if __name__ == "__main__":
    unittest.main()
