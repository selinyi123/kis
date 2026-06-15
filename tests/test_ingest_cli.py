"""KIS-018 CLI tests (offline)."""

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

import ingest_external as cli  # noqa: E402
from kis.store import Store  # noqa: E402

_FIXDIR = os.path.join(_ROOT, "tests", "fixtures")


class TestIngestCli(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
        self.db = os.path.join(self.tmp, "k.db")
        self.vault = os.path.join(self.tmp, "v")

    def _run(self, *argv):
        with redirect_stdout(io.StringIO()):
            sys.argv = ["ingest_external.py", *argv]
            return cli.main()

    def test_dry_run_writes_nothing(self):
        rc = self._run("github-stars", "--input", os.path.join(_FIXDIR, "github_stars.json"),
                       "--db-path", self.db, "--obsidian-dir", self.vault, "--dry-run")
        self.assertEqual(rc, 0)
        self.assertEqual(Store(self.db).count(), 0)
        self.assertFalse(os.path.exists(os.path.join(self.vault, "External-Inbox")))

    def test_three_sources_real_run(self):
        cwd = os.getcwd(); os.chdir(self.tmp); self.addCleanup(os.chdir, cwd)
        self._run("github-stars", "--input", os.path.join(_FIXDIR, "github_stars.json"),
                  "--db-path", self.db, "--obsidian-dir", self.vault)
        self._run("bookmarks", "--input", os.path.join(_FIXDIR, "bookmarks.html"),
                  "--db-path", self.db, "--obsidian-dir", self.vault)
        self._run("web-clips", "--input", os.path.join(_FIXDIR, "web_clips.jsonl"),
                  "--db-path", self.db, "--obsidian-dir", self.vault)
        s = Store(self.db)
        self.assertEqual(s.count("github_star"), 2)
        self.assertEqual(s.count("web_bookmark"), 3)
        self.assertEqual(s.count("web_clip"), 1)
        self.assertEqual(self._run("report"), 0)


if __name__ == "__main__":
    unittest.main()
