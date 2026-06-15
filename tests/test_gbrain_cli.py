"""KIS-016 CLI tests (offline, mock adapter)."""

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
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import gbrain_trial as cli  # noqa: E402
from gbrain_fixtures import make_vault  # noqa: E402


class TestGbrainCli(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
        self.vault = make_vault(self.tmp)
        self.out = os.path.join(self.tmp, "out")

    def _run(self, *argv):
        buf = io.StringIO()
        with redirect_stdout(buf):
            sys.argv = ["gbrain_trial.py", *argv, "--vault-dir", self.vault, "--out-dir", self.out]
            return cli.main()

    def test_export_dry_run_writes_nothing(self):
        self.assertEqual(self._run("export", "--dry-run"), 0)
        self.assertFalse(os.path.exists(os.path.join(self.out, "exported_vault")))

    def test_all_pipeline_mock(self):
        self.assertEqual(self._run("all", "--adapter", "mock"), 0)
        run_dir = os.path.join(self.out, "runs", "latest")
        for fn in ("baseline_results.jsonl", "gbrain_results.jsonl", "evaluation.json", "trial_report.md"):
            self.assertTrue(os.path.exists(os.path.join(run_dir, fn)), fn)
        self.assertTrue(os.path.exists(os.path.join(self.out, "exported_vault")))

    def test_individual_commands(self):
        for argv in (("export",), ("questions",), ("baseline",), ("run", "--adapter", "mock"),
                     ("evaluate",), ("report",)):
            self.assertEqual(self._run(*argv), 0, argv)

    def test_manual_template_then_manual_run(self):
        import json
        self._run("export")
        self._run("baseline")
        self.assertEqual(self._run("manual-template"), 0)
        tmpl = os.path.join(self.out, "runs", "latest", "gbrain_manual_input.jsonl")
        self.assertTrue(os.path.exists(tmpl))
        with open(tmpl, encoding="utf-8") as fh:
            rows = [json.loads(ln) for ln in fh if ln.strip()]
        self.assertEqual(len(rows), 20)
        self.assertTrue(all("answer" in r and "citations" in r for r in rows))
        # a filled template is consumable by the manual adapter
        self.assertEqual(self._run("run", "--adapter", "manual"), 0)


if __name__ == "__main__":
    unittest.main()
