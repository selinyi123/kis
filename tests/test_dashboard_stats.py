"""KIS-015 stats tests (pure)."""

import os
import sys
import unittest

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(_ROOT, "src"))

from kis.card import github_star_card  # noqa: E402
from kis.enrich.heuristic import enrich_card  # noqa: E402
from kis.dashboard.stats import compute_review_stats  # noqa: E402

_i = [0]


def mk(state="inbox", enrich_it=True):
    _i[0] += 1
    c = github_star_card({"full_name": f"x/y{_i[0]}", "html_url": f"https://github.com/x/y{_i[0]}",
                          "description": "memory", "language": "Py", "stargazers_count": 1, "topics": ["memory"]})
    if enrich_it:
        c = enrich_card(c)
    c["lifecycle"]["state"] = state
    return c


class TestStats(unittest.TestCase):
    def test_stats_by_lifecycle(self):
        s = compute_review_stats([mk("inbox"), mk("inbox"), mk("canonical")])
        self.assertEqual(s["by_lifecycle"]["inbox"], 2)
        self.assertEqual(s["by_lifecycle"]["canonical"], 1)
        self.assertEqual(s["total"], 3)

    def test_stats_by_source_type(self):
        s = compute_review_stats([mk(), mk()])
        self.assertEqual(s["by_source_type"]["github_star"], 2)

    def test_stats_by_value_level(self):
        s = compute_review_stats([mk(), mk()])
        self.assertEqual(sum(s["by_value_level"].values()), 2)

    def test_stats_missing_derived_does_not_crash(self):
        s = compute_review_stats([mk(enrich_it=False)])
        self.assertEqual(s["by_value_level"].get("unknown"), 1)
        self.assertEqual(s["by_next_action"].get("unknown"), 1)

    def test_stats_excludes_blocked(self):
        c = mk(); c["safety"]["sensitivity"] = "blocked"
        self.assertEqual(compute_review_stats([c])["total"], 0)


if __name__ == "__main__":
    unittest.main()
