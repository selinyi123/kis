"""KIS-018 report rendering tests."""

import os
import sys
import unittest

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(_ROOT, "src"))

from kis.ingest.models import IngestReport  # noqa: E402
from kis.ingest.report import render_markdown  # noqa: E402


class TestIngestReport(unittest.TestCase):
    def test_sections_and_counts(self):
        rep = IngestReport(source_type="github_star", input_file="x.json",
                           total_seen=4, created=2, skipped_duplicate=1, blocked=1, errors=0)
        rep.created_cards = [{"id": "kc_1", "title": "a|b pipe", "url": "https://x/y"}]
        rep.blocked_items = [{"url": "https://leak", "reason": "secret:github_token"}]
        md = render_markdown(rep)
        for sec in ("# KIS-018 Ingestion Report", "## Summary", "## Created Cards",
                    "## Duplicates", "## Blocked", "## Errors", "## Next Review Actions"):
            self.assertIn(sec, md)
        self.assertIn("| total_seen | 4 |", md)
        self.assertIn("| blocked | 1 |", md)
        self.assertIn("a\\|b pipe", md)  # pipe escaped


if __name__ == "__main__":
    unittest.main()
