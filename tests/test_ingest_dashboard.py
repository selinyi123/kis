"""KIS-018 dashboard external-inbox stats tests."""

import os
import shutil
import sys
import tempfile
import unittest

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(_ROOT, "src"))

from kis.dashboard.stats import compute_review_stats  # noqa: E402
from kis.ingest import runner  # noqa: E402
from kis.store import Store  # noqa: E402

_FIXDIR = os.path.join(_ROOT, "tests", "fixtures")


class TestIngestDashboard(unittest.TestCase):
    def test_external_inbox_stats_by_source_type(self):
        tmp = tempfile.mkdtemp(); self.addCleanup(shutil.rmtree, tmp, ignore_errors=True)
        db = os.path.join(tmp, "k.db")
        runner.ingest("github-stars", os.path.join(_FIXDIR, "github_stars.json"), Store(db), None)
        runner.ingest("bookmarks", os.path.join(_FIXDIR, "bookmarks.html"), Store(db), None)
        stats = compute_review_stats(Store(db).all_cards())
        ext = stats["external_inbox"]
        self.assertEqual(ext["total"], 5)                       # 2 stars + 3 bookmarks
        self.assertEqual(ext["by_source_type"]["github_star"], 2)
        self.assertEqual(ext["by_source_type"]["web_bookmark"], 3)


if __name__ == "__main__":
    unittest.main()
