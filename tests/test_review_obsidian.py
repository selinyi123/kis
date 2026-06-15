"""KIS-014 Obsidian review-block rendering."""

import os
import sys
import unittest

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(_ROOT, "src"))

from kis.card import github_star_card  # noqa: E402
from kis.enrich.heuristic import enrich_card  # noqa: E402
from kis.obsidian import render_card_md  # noqa: E402
from kis.review.actions import apply_review  # noqa: E402

_REPO = {"full_name": "x/y", "html_url": "https://github.com/x/y", "description": "memory",
         "language": "Python", "stargazers_count": 1, "topics": ["memory"]}


class TestReviewObsidian(unittest.TestCase):
    def test_pending_review_block_for_unreviewed_card(self):
        md = render_card_md(enrich_card(github_star_card(_REPO)))
        self.assertIn("## Review", md)
        self.assertIn("Status: inbox", md)
        self.assertIn("Decision: pending", md)

    def test_review_block_renders_decision_and_hashes(self):
        card = enrich_card(github_star_card(_REPO))
        out, _ = apply_review(card, "reviewed", "verified source")
        md = render_card_md(out)
        self.assertIn("## Review", md)
        self.assertIn("| Status | reviewed |", md)
        self.assertIn("| Decision | reviewed |", md)
        self.assertIn("| Review Hash |", md)
        # source/derived sections still present and not overwritten
        self.assertIn("## Derived Intelligence", md)
        self.assertIn("**来源**", md)


if __name__ == "__main__":
    unittest.main()
