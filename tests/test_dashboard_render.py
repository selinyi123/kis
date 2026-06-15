"""KIS-015 render tests — safety, escaping, no-approve-on-inbox."""

import os
import sys
import unittest

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(_ROOT, "src"))

from kis.card import github_star_card  # noqa: E402
from kis.enrich.heuristic import enrich_card  # noqa: E402
from kis.dashboard import render  # noqa: E402

_TS = "2026-06-15T00:00:00Z"


def _base():
    return github_star_card({"full_name": "x/y", "html_url": "https://github.com/x/y",
                             "description": "memory", "language": "Py", "stargazers_count": 1, "topics": ["memory"]})


class TestRender(unittest.TestCase):
    def test_missing_derived_shows_unknown_not_crash(self):
        md = render.render_inbox([_base()], _TS)  # no derived
        self.assertIn("unknown", md)

    def test_missing_review_shows_pending(self):
        md = render.render_inbox([enrich_card(_base())], _TS)
        self.assertIn("| Review | pending |", md)

    def test_table_pipe_is_escaped(self):
        c = enrich_card(_base())
        c["content"]["title"] = "a|b"
        md = render.render_inbox([c], _TS)
        self.assertIn("a\\|b", md)
        self.assertNotIn("| a|b |", md)

    def test_suggested_commands_include_reason(self):
        md = render.render_inbox([enrich_card(_base())], _TS)
        self.assertIn("--card-id", md)
        self.assertIn("--reason", md)

    def test_inbox_page_has_no_approve_command(self):
        md = render.render_inbox([enrich_card(_base())], _TS)
        self.assertNotIn("approve", md)
        self.assertNotIn("canonical", md)

    def test_canonical_page_uses_approve(self):
        c = enrich_card(_base()); c["lifecycle"]["state"] = "reviewed"
        c["derived"]["value_level"] = "hot"; c["derived"]["next_action"] = "integrate"
        md = render.render_canonical([c], _TS)
        self.assertIn("approve --card-id", md)

    def test_rejected_page_has_no_approve(self):
        c = enrich_card(_base()); c["lifecycle"]["state"] = "rejected"
        md = render.render_rejected([c], _TS)
        self.assertNotIn("approve", md)


if __name__ == "__main__":
    unittest.main()
