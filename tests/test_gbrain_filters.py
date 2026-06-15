"""KIS-016 safe-export filter tests."""

import os
import sys
import unittest

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(_ROOT, "src"))

from kis.gbrain_trial.filters import classify_file  # noqa: E402


class TestFilters(unittest.TestCase):
    def test_allowlisted_markdown_allowed(self):
        self.assertTrue(classify_file("GitHub-Stars/MemTensor-MemOS.md", 500, b"# md").allowed)
        self.assertTrue(classify_file("01 架构.md", 500, b"# md").allowed)  # root note

    def test_deny_pattern_tokens(self):
        for p in ("secret/notes.md", "x/token.md", "creds/cookie.md", "Web-Clips/session-keys.md"):
            self.assertFalse(classify_file(p, 100, b"x").allowed, p)

    def test_blocked_confidential_private(self):
        for p in ("_blocked/x.md", "confidential/x.md", "private/x.md"):
            self.assertFalse(classify_file(p, 100, b"x").allowed, p)

    def test_binary_db_env_key_denied(self):
        self.assertFalse(classify_file("data.db", 100, b"x").allowed)
        self.assertFalse(classify_file("a/.env", 100, b"x").allowed)
        self.assertFalse(classify_file("a/server.pem", 100, b"x").allowed)
        self.assertFalse(classify_file("GitHub-Stars/x.md", 100, b"\x00\x01bin").allowed)  # binary

    def test_dir_not_allowlisted_denied(self):
        self.assertFalse(classify_file("RandomFolder/note.md", 100, b"x").allowed)

    def test_too_large_denied(self):
        self.assertFalse(classify_file("GitHub-Stars/x.md", 2_000_000, b"x").allowed)

    def test_json_denied_unless_allowlisted(self):
        self.assertFalse(classify_file("GitHub-Stars/data.json", 100, b"{}").allowed)

    def test_internal_sensitivity_tag(self):
        r = classify_file("Browser-Bookmarks/Ops-Internal/x.md", 100, b"x")
        self.assertTrue(r.allowed)
        self.assertEqual(r.sensitivity, "internal")


if __name__ == "__main__":
    unittest.main()
