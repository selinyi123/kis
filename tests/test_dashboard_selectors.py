"""KIS-015 selector tests (pure)."""

import os
import sys
import unittest

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(_ROOT, "src"))

from kis.card import github_star_card  # noqa: E402
from kis.enrich.heuristic import enrich_card  # noqa: E402
from kis.dashboard.selectors import (  # noqa: E402
    select_archive_candidates, select_canonical_candidates, select_deferred_cards,
    select_inbox_cards, select_rejected_cards, sort_review_cards,
)

_i = [0]


def mk(state="inbox", vl="hot", na="integrate", blocked=False, enrich_it=True):
    _i[0] += 1
    c = github_star_card({"full_name": f"x/y{_i[0]}", "html_url": f"https://github.com/x/y{_i[0]}",
                          "description": "memory agent", "language": "Py", "stargazers_count": 1, "topics": ["memory"]})
    if enrich_it:
        c = enrich_card(c)
        if vl:
            c["derived"]["value_level"] = vl
        if na:
            c["derived"]["next_action"] = na
    c["lifecycle"]["state"] = state
    if blocked:
        c["safety"]["sensitivity"] = "blocked"
    return c


class TestSelectors(unittest.TestCase):
    def test_inbox_selector(self):
        cards = [mk("inbox"), mk("reviewed"), mk("inbox", blocked=True)]
        out = select_inbox_cards(cards)
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0]["lifecycle"]["state"], "inbox")

    def test_canonical_candidates_exclude_inbox(self):
        cards = [mk("inbox", "hot", "integrate"), mk("reviewed", "hot", "integrate")]
        out = select_canonical_candidates(cards)
        self.assertTrue(all(c["lifecycle"]["state"] == "reviewed" for c in out))
        self.assertEqual(len(out), 1)

    def test_canonical_candidates_only_hot_or_critical_integrate_or_test(self):
        cards = [mk("reviewed", "warm", "integrate"), mk("reviewed", "hot", "read"),
                 mk("reviewed", "critical", "test"), mk("reviewed", "hot", "integrate")]
        out = select_canonical_candidates(cards)
        self.assertEqual(len(out), 2)  # critical/test + hot/integrate only

    def test_archive_candidates_exclude_canonical(self):
        cards = [mk("canonical", "cold", "archive"), mk("inbox", "cold", "read"),
                 mk("inbox", "warm", "archive"), mk("rejected", "hot", "integrate")]
        out = select_archive_candidates(cards)
        self.assertTrue(all(c["lifecycle"]["state"] != "canonical" for c in out))
        self.assertEqual(len(out), 3)  # cold + archive + rejected

    def test_deferred_and_rejected_selectors(self):
        cards = [mk("deferred"), mk("rejected"), mk("inbox")]
        self.assertEqual(len(select_deferred_cards(cards)), 1)
        self.assertEqual(len(select_rejected_cards(cards)), 1)

    def test_sort_is_stable_and_prioritized(self):
        cards = [mk("inbox", "cold", "ignore"), mk("inbox", "critical", "integrate"),
                 mk("inbox", "hot", "test")]
        out = sort_review_cards(cards)
        levels = [c["derived"]["value_level"] for c in out]
        self.assertEqual(levels, ["critical", "hot", "cold"])
        # deterministic
        self.assertEqual([c["id"] for c in sort_review_cards(cards)], [c["id"] for c in out])


if __name__ == "__main__":
    unittest.main()
