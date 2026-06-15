"""KIS-015 safety — dashboard is read-only: never mutates store/lifecycle/review."""

import io
import json
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
from kis.dashboard import commands  # noqa: E402
from kis.store import Store  # noqa: E402
import build_review_dashboard as brd  # noqa: E402


class TestDashboardSafety(unittest.TestCase):
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

    def _snapshot(self):
        return {c["id"]: json.dumps(c, sort_keys=True) for c in Store(self.db).all_cards()}

    def test_build_does_not_modify_store(self):
        before = self._snapshot()
        out = io.StringIO()
        with redirect_stdout(out):
            sys.argv = ["x", "--db-path", self.db, "--obsidian-dir", self.vault]
            brd.main()
        after = self._snapshot()
        self.assertEqual(before, after)  # store byte-for-byte unchanged

    def test_build_does_not_change_lifecycle_or_review(self):
        before = {c["id"]: (c["lifecycle"]["state"], c.get("review")) for c in Store(self.db).all_cards()}
        out = io.StringIO()
        with redirect_stdout(out):
            sys.argv = ["x", "--db-path", self.db, "--obsidian-dir", self.vault]
            brd.main()
        after = {c["id"]: (c["lifecycle"]["state"], c.get("review")) for c in Store(self.db).all_cards()}
        self.assertEqual(before, after)

    def test_rejected_commands_have_no_approve(self):
        c = enrich_card(github_star_card(
            {"full_name": "a/r", "html_url": "https://github.com/a/r", "description": "d",
             "language": "Py", "stargazers_count": 1, "topics": []}))
        self.assertEqual(commands.rejected_commands(c), [])


if __name__ == "__main__":
    unittest.main()
