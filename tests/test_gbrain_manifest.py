"""KIS-016 manifest + hashing tests."""

import os
import sys
import unittest

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(_ROOT, "src"))

from kis.gbrain_trial.manifest import build_manifest, content_hash  # noqa: E402


class TestManifest(unittest.TestCase):
    def test_content_hash_stable(self):
        self.assertEqual(content_hash(b"hello"), content_hash(b"hello"))
        self.assertNotEqual(content_hash(b"a"), content_hash(b"b"))

    def test_build_manifest_summary(self):
        inc = [{"source_path": "a.md", "size_bytes": 10}, {"source_path": "b.md", "size_bytes": 20}]
        den = [{"source_path": "secret/x.md", "reason": "deny pattern: secret"}]
        m = build_manifest("vault", "exp", inc, den)
        self.assertEqual(m["summary"]["included_count"], 2)
        self.assertEqual(m["summary"]["denied_count"], 1)
        self.assertEqual(m["summary"]["total_bytes"], 30)
        self.assertIn("generated_at", m)


if __name__ == "__main__":
    unittest.main()
