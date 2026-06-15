"""KIS-014 immutability — review never touches the factual core."""

import copy
import os
import sys
import unittest

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(_ROOT, "src"))

from kis.card import github_star_card  # noqa: E402
from kis.enrich.heuristic import enrich_card  # noqa: E402
from kis.review.actions import apply_review  # noqa: E402

_REPO = {"full_name": "x/y", "html_url": "https://github.com/x/y", "description": "memory agent rag",
         "language": "Python", "stargazers_count": 9, "topics": ["memory", "rag"]}

_LOCKED = ("source", "content", "enrichment", "linkage", "safety", "derived")


class TestReviewImmutability(unittest.TestCase):
    def test_review_does_not_change_factual_core(self):
        card = enrich_card(github_star_card(_REPO))
        before = {k: copy.deepcopy(card[k]) for k in _LOCKED}
        out, _ = apply_review(card, "reviewed", "verified source and relevance")
        for k in _LOCKED:
            self.assertEqual(out[k], before[k], f"{k} changed by review")

    def test_original_card_not_mutated_in_place(self):
        card = enrich_card(github_star_card(_REPO))
        snapshot = copy.deepcopy(card)
        apply_review(card, "reviewed", "ok")
        self.assertEqual(card, snapshot)  # apply_review returns a copy, no in-place edit

    def test_canonical_keeps_source_hash_equal_to_content_hash(self):
        card = enrich_card(github_star_card(_REPO))
        card["lifecycle"]["state"] = "reviewed"
        out, _ = apply_review(card, "approve_canonical", "promote")
        self.assertEqual(out["review"]["source_hash"], card["content_hash"])


if __name__ == "__main__":
    unittest.main()
