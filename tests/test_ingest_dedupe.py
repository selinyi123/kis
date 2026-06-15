"""KIS-018 dedupe + dry-run/real consistency + idempotency tests."""

import os
import shutil
import sys
import tempfile
import unittest

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(_ROOT, "src"))

from kis.card import github_star_card  # noqa: E402
from kis.ingest import runner  # noqa: E402
from kis.ingest.dedupe import Deduper  # noqa: E402
from kis.store import Store  # noqa: E402

_FIX = os.path.join(_ROOT, "tests", "fixtures", "github_stars.json")


class TestDedupe(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
        self.db = os.path.join(self.tmp, "k.db")

    def test_within_run_dedupe_keys(self):
        d = Deduper(None)
        c = github_star_card({"full_name": "x/y", "html_url": "https://github.com/x/y", "description": "d"})
        self.assertEqual(d.status(c), "new")
        self.assertEqual(d.status(c), "duplicate")  # same url/hash/source_id

    def test_dry_run_matches_real_counts(self):
        dry = runner.ingest("github-stars", _FIX, Store(self.db), None, dry_run=True)
        real = runner.ingest("github-stars", _FIX, Store(self.db), None, dry_run=False)
        self.assertEqual((dry.created, dry.skipped_duplicate, dry.blocked, dry.errors),
                         (real.created, real.skipped_duplicate, real.blocked, real.errors))

    def test_reimport_is_idempotent(self):
        runner.ingest("github-stars", _FIX, Store(self.db), None)
        rep2 = runner.ingest("github-stars", _FIX, Store(self.db), None)
        self.assertEqual(rep2.created, 0)
        self.assertGreaterEqual(rep2.skipped_duplicate, 2)
        self.assertEqual(Store(self.db).count("github_star"), 2)


if __name__ == "__main__":
    unittest.main()
