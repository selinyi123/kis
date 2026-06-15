"""KIS-015 CLI tests — dry-run, file generation, idempotency."""

import io
import os
import shutil
import sys
import tempfile
import unittest
from contextlib import redirect_stdout

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(_ROOT, "src"))
sys.path.insert(0, os.path.join(_ROOT, "scripts"))

from kis.card import github_star_card  # noqa: E402
from kis.enrich.heuristic import enrich_card  # noqa: E402
from kis.store import Store  # noqa: E402
import build_review_dashboard as brd  # noqa: E402

_TS = "2026-06-15T00:00:00Z"


class TestDashboardCli(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
        self.db = os.path.join(self.tmp, "k.db")
        self.vault = os.path.join(self.tmp, "v")
        s = Store(self.db)
        for i in range(3):
            s.upsert(enrich_card(github_star_card(
                {"full_name": f"a/b{i}", "html_url": f"https://github.com/a/b{i}",
                 "description": "memory", "language": "Py", "stargazers_count": 1, "topics": ["memory"]})))
        s.close()

    def _run(self, argv):
        out = io.StringIO()
        with redirect_stdout(out):
            sys.argv = ["build_review_dashboard.py", "--db-path", self.db, "--obsidian-dir", self.vault, *argv]
            return brd.main()

    def test_dry_run_writes_no_files(self):
        self.assertEqual(self._run(["--dry-run"]), 0)
        self.assertFalse(os.path.isdir(os.path.join(self.vault, "Dashboards")))

    def test_build_generates_all_pages(self):
        self.assertEqual(self._run([]), 0)
        d = os.path.join(self.vault, "Dashboards")
        files = set(os.listdir(d))
        for f in ("KIS Review Dashboard.md", "Review Inbox.md", "Canonical Candidates.md",
                  "Archive Candidates.md", "Deferred Queue.md", "Rejected Queue.md", "Review Stats.md"):
            self.assertIn(f, files)

    def test_only_flag_builds_single_page(self):
        self.assertEqual(self._run(["--only", "stats"]), 0)
        self.assertEqual(os.listdir(os.path.join(self.vault, "Dashboards")), ["Review Stats.md"])

    def test_build_pages_is_idempotent(self):
        cards = Store(self.db).load_dashboard_cards()
        self.assertEqual(brd.build_pages(cards, _TS), brd.build_pages(cards, _TS))


if __name__ == "__main__":
    unittest.main()
