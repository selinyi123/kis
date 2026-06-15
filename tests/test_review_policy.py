"""KIS-014 policy + apply_review tests (pure, offline)."""

import os
import sys
import unittest

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(_ROOT, "src"))

from kis.card import github_star_card  # noqa: E402
from kis.enrich.heuristic import enrich_card  # noqa: E402
from kis.review.actions import ReviewError, apply_review  # noqa: E402
from kis.review.models import review_hash  # noqa: E402
from kis.review.policy import IllegalTransition, is_legal  # noqa: E402

_REPO = {"full_name": "x/y", "html_url": "https://github.com/x/y", "description": "memory agent",
         "language": "Python", "stargazers_count": 1, "topics": ["memory"]}


def _card(state="inbox", enrich=True):
    c = github_star_card(_REPO)
    if enrich:
        c = enrich_card(c)
    c["lifecycle"]["state"] = state
    return c


class TestPolicy(unittest.TestCase):
    def test_legal_transition(self):
        self.assertTrue(is_legal("inbox", "reviewed"))
        self.assertTrue(is_legal("reviewed", "canonical"))
        self.assertTrue(is_legal("deferred", "reviewed"))

    def test_illegal_transition_rejected(self):
        self.assertFalse(is_legal("inbox", "canonical"))
        self.assertFalse(is_legal("canonical", "inbox"))
        self.assertFalse(is_legal("archived", "canonical"))

    def test_inbox_cannot_go_canonical(self):
        with self.assertRaises(IllegalTransition):
            apply_review(_card("inbox"), "approve_canonical", "x")

    def test_reviewed_can_go_canonical(self):
        out, changed = apply_review(_card("reviewed"), "approve_canonical", "promote")
        self.assertTrue(changed)
        self.assertEqual(out["lifecycle"]["state"], "canonical")
        self.assertEqual(out["review"]["next_status"], "canonical")

    def test_archived_and_rejected_cannot_go_canonical(self):
        for st in ("archived", "rejected"):
            with self.assertRaises(IllegalTransition):
                apply_review(_card(st), "approve_canonical", "x")

    def test_review_hash_is_stable(self):
        kw = dict(card_id="kc_1", previous_status="inbox", next_status="reviewed", decision="reviewed",
                  reason="r", reviewer="human", reviewed_at="2026-06-15T00:00:00Z",
                  source_hash="s", derived_hash="d")
        self.assertEqual(review_hash(**kw), review_hash(**kw))
        self.assertNotEqual(review_hash(**kw), review_hash(**{**kw, "reason": "other"}))

    def test_idempotent_noop(self):
        out, changed = apply_review(_card("reviewed"), "reviewed", "again")
        self.assertFalse(changed)

    def test_reason_must_not_be_empty(self):
        for bad in ("", "   "):
            with self.assertRaises(ReviewError):
                apply_review(_card("inbox"), "reviewed", bad)

    def test_reviewer_defaults_human(self):
        out, _ = apply_review(_card("inbox"), "reviewed", "ok")
        self.assertEqual(out["review"]["reviewer"], "human")

    def test_derived_missing_still_reviewable(self):
        out, changed = apply_review(_card("reviewed", enrich=False), "approve_canonical", "human reason")
        self.assertTrue(changed)
        self.assertEqual(out["review"]["derived_hash"], "none")

    def test_blocked_card_refused(self):
        c = _card("inbox")
        c["safety"]["sensitivity"] = "blocked"
        with self.assertRaises(ReviewError):
            apply_review(c, "reviewed", "x")


if __name__ == "__main__":
    unittest.main()
