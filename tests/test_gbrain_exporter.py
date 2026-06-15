"""KIS-016 exporter tests."""

import os
import shutil
import sys
import tempfile
import unittest

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(_ROOT, "src"))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from kis.gbrain_trial.exporter import export_vault  # noqa: E402
from gbrain_fixtures import allowed_count, make_vault  # noqa: E402


class TestExporter(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
        self.vault = make_vault(self.tmp)
        self.out = os.path.join(self.tmp, "out")

    def test_export_includes_allowed_excludes_denied(self):
        m = export_vault(self.vault, self.out)
        self.assertEqual(m["summary"]["included_count"], allowed_count())
        self.assertGreaterEqual(m["summary"]["denied_count"], 6)
        inc = {f["source_path"] for f in m["included_files"]}
        self.assertIn("GitHub-Stars/MemTensor-MemOS.md", inc)
        self.assertNotIn("secret/token.md", inc)
        self.assertNotIn("DPMS-Platform/cookie-token.md", inc)
        # exported files physically present; denied absent
        self.assertTrue(os.path.exists(os.path.join(self.out, "exported_vault", "GitHub-Stars", "MemTensor-MemOS.md")))
        self.assertFalse(os.path.exists(os.path.join(self.out, "exported_vault", "secret", "token.md")))

    def test_dry_run_writes_nothing(self):
        m = export_vault(self.vault, self.out, dry_run=True)
        self.assertEqual(m["summary"]["included_count"], allowed_count())
        self.assertFalse(os.path.exists(os.path.join(self.out, "exported_vault")))
        self.assertFalse(os.path.exists(os.path.join(self.out, "manifests")))

    def test_manifest_files_written(self):
        export_vault(self.vault, self.out)
        for fn in ("export_manifest.json", "denied_files.json", "content_hashes.json"):
            self.assertTrue(os.path.exists(os.path.join(self.out, "manifests", fn)))


if __name__ == "__main__":
    unittest.main()
