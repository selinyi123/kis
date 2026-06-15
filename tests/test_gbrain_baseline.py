"""KIS-016 baseline search tests."""

import os
import shutil
import sys
import tempfile
import unittest

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(_ROOT, "src"))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from kis.gbrain_trial.baseline_search import load_docs, search  # noqa: E402
from kis.gbrain_trial.exporter import export_vault  # noqa: E402
from gbrain_fixtures import make_vault  # noqa: E402


class TestBaseline(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
        export_vault(make_vault(self.tmp), os.path.join(self.tmp, "out"))
        self.docs = load_docs(os.path.join(self.tmp, "out", "exported_vault"))

    def test_search_returns_explainable_results(self):
        res = search("ClipVault Obsidian 记忆", self.docs, top_k=3)
        self.assertTrue(res)
        top = res[0]
        self.assertIn("path", top)
        self.assertIn("score", top)
        self.assertIn("snippet", top)
        self.assertGreater(top["score"], 0)

    def test_search_empty_docs(self):
        self.assertEqual(search("anything", [], top_k=3), [])

    def test_search_no_match_returns_empty(self):
        self.assertEqual(search("zzzzqqqxx", self.docs, top_k=3), [])


if __name__ == "__main__":
    unittest.main()
