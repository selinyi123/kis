"""KIS-018 secret-guard tests."""

import os
import shutil
import sys
import tempfile
import unittest

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(_ROOT, "src"))

from kis.ingest import runner  # noqa: E402
from kis.ingest.safety import is_blocked, scan_secrets  # noqa: E402
from kis.store import Store  # noqa: E402


class TestSafety(unittest.TestCase):
    def test_detects_openai_key(self):
        self.assertIn("openai_key", scan_secrets("here is sk-ABCDEFGHIJKLMNOPQRSTUV more"))

    def test_detects_github_token(self):
        self.assertIn("github_token", scan_secrets("ghp_ABCDEFGHIJKLMNOPQRSTUVWX"))

    def test_detects_private_key(self):
        self.assertTrue(is_blocked("-----BEGIN RSA PRIVATE KEY-----")[0])

    def test_clean_text_not_blocked(self):
        self.assertFalse(is_blocked("a normal article about knowledge graphs")[0])

    def test_blocked_secret_not_written_to_store_or_vault(self):
        tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, tmp, ignore_errors=True)
        db = os.path.join(tmp, "k.db"); vault = os.path.join(tmp, "v")
        clip = os.path.join(tmp, "c.jsonl")
        with open(clip, "w", encoding="utf-8") as fh:
            fh.write('{"url":"https://x.com/leak","title":"L","text":"key sk-ABCDEFGHIJKLMNOPQRSTUV"}\n')
        rep = runner.ingest("web-clips", clip, Store(db), vault)
        self.assertEqual(rep.blocked, 1)
        self.assertEqual(Store(db).count(), 0)
        # nothing under External-Inbox
        self.assertFalse(os.path.exists(os.path.join(vault, "External-Inbox")))


if __name__ == "__main__":
    unittest.main()
