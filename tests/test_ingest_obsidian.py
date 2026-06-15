"""KIS-018 External-Inbox Obsidian rendering tests."""

import os
import shutil
import sys
import tempfile
import unittest

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(_ROOT, "src"))

from kis.ingest import runner  # noqa: E402
from kis.ingest.normalizer import build_card  # noqa: E402
from kis.obsidian import render_external_inbox_md  # noqa: E402
from kis.store import Store  # noqa: E402

_FIX = os.path.join(_ROOT, "tests", "fixtures", "github_stars.json")


class TestIngestObsidian(unittest.TestCase):
    def test_render_sections_and_no_approve(self):
        card = build_card("github_star", {"full_name": "x/y", "html_url": "https://github.com/x/y",
                                          "description": "memory"})
        md = render_external_inbox_md(card)
        for sec in ("## Source", "## Content", "## Safety", "## Lifecycle", "## Review",
                    "## Suggested Review Commands"):
            self.assertIn(sec, md)
        self.assertNotIn("approve", md)          # inbox: never approve
        for cmd in ("mark-reviewed", "archive", "defer", "reject"):
            self.assertIn(cmd, md)

    def test_ingest_writes_external_inbox_files(self):
        tmp = tempfile.mkdtemp(); self.addCleanup(shutil.rmtree, tmp, ignore_errors=True)
        vault = os.path.join(tmp, "v")
        runner.ingest("github-stars", _FIX, Store(os.path.join(tmp, "k.db")), vault)
        gh_dir = os.path.join(vault, "External-Inbox", "GitHub-Stars")
        self.assertTrue(os.path.isdir(gh_dir))
        self.assertTrue([f for f in os.listdir(gh_dir) if f.endswith(".md")])


if __name__ == "__main__":
    unittest.main()
