"""KIS-016 adapter tests — mock/manual offline; subprocess degrades cleanly."""

import json
import os
import shutil
import sys
import tempfile
import unittest

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(_ROOT, "src"))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from kis.gbrain_trial.adapters import (  # noqa: E402
    AdapterUnavailable, ManualGBrainAdapter, MockGBrainAdapter, SubprocessGBrainAdapter,
)
from kis.gbrain_trial.exporter import export_vault  # noqa: E402
from gbrain_fixtures import make_vault  # noqa: E402


class TestAdapters(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
        m = export_vault(make_vault(self.tmp), os.path.join(self.tmp, "out"))
        self.export_dir = os.path.join(self.tmp, "out", "exported_vault")
        self.exported = {f["source_path"] for f in m["included_files"]}

    def test_mock_adapter_runs_offline_with_traceable_citations(self):
        a = MockGBrainAdapter(self.export_dir)
        a.index()
        ans = a.ask("q001", "ClipVault 与 Obsidian 记忆 知识库")
        self.assertTrue(ans.citations)
        for c in ans.citations:
            self.assertIn(c["path"], self.exported)  # cites only exported files
        self.assertNotIn("openai", sys.modules)

    def test_mock_unknown_when_no_match(self):
        a = MockGBrainAdapter(self.export_dir); a.index()
        ans = a.ask("q999", "zzzqqq nonexistent topic")
        self.assertIn("unknown", ans.answer.lower())
        self.assertEqual(ans.citations, [])

    def test_manual_adapter_reads_jsonl(self):
        path = os.path.join(self.tmp, "manual.jsonl")
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(json.dumps({"question_id": "q001", "answer": "manual ans",
                                 "citations": [{"path": "01 架构.md"}]}) + "\n")
        a = ManualGBrainAdapter(path); a.index()
        self.assertEqual(a.ask("q001", "x").answer, "manual ans")

    def test_subprocess_adapter_unavailable_graceful(self):
        a = SubprocessGBrainAdapter(self.export_dir, binary="definitely-not-a-real-binary-xyz")
        with self.assertRaises(AdapterUnavailable):
            a.index()


if __name__ == "__main__":
    unittest.main()
