"""KIS-016 safety — read-only isolation, sensitive exclusion, no writeback."""

import hashlib
import os
import shutil
import sys
import tempfile
import unittest

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(_ROOT, "src"))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from kis.gbrain_trial.exporter import export_vault  # noqa: E402
from gbrain_fixtures import make_vault  # noqa: E402


def _tree_hash(root):
    h = {}
    for r, _d, fs in os.walk(root):
        for f in fs:
            p = os.path.join(r, f)
            with open(p, "rb") as fh:
                h[os.path.relpath(p, root)] = hashlib.sha256(fh.read()).hexdigest()
    return h


class TestGbrainSafety(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
        self.vault = make_vault(self.tmp)
        self.out = os.path.join(self.tmp, "out")

    def test_dpms_credentials_not_exported(self):
        m = export_vault(self.vault, self.out)
        inc = {f["source_path"] for f in m["included_files"]}
        self.assertNotIn("DPMS-Platform/cookie-token.md", inc)
        self.assertNotIn("browser-profile/qr-session.md", inc)
        self.assertNotIn("creds/credential.txt", inc)
        # but desensitized DPMS public doc IS allowed
        self.assertIn("DPMS-Platform/脱敏复盘.md", inc)

    def test_source_vault_unchanged_after_export(self):
        before = _tree_hash(self.vault)
        export_vault(self.vault, self.out)
        after = _tree_hash(self.vault)
        self.assertEqual(before, after)  # read-only w.r.t. source vault

    def test_export_only_contains_allowed_files(self):
        export_vault(self.vault, self.out)
        exp = os.path.join(self.out, "exported_vault")
        for r, _d, fs in os.walk(exp):
            for f in fs:
                low = os.path.join(r, f).lower()
                for bad in ("secret", "token", "cookie", "qr", "session", ".env", ".db"):
                    self.assertNotIn(bad, low)


if __name__ == "__main__":
    unittest.main()
