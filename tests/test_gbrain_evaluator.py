"""KIS-016 evaluator tests."""

import os
import shutil
import sys
import tempfile
import unittest

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(_ROOT, "src"))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from kis.gbrain_trial.adapters import MockGBrainAdapter  # noqa: E402
from kis.gbrain_trial.evaluator import evaluate  # noqa: E402
from kis.gbrain_trial.exporter import export_vault  # noqa: E402
from kis.gbrain_trial import baseline_search  # noqa: E402
from gbrain_fixtures import make_vault  # noqa: E402

_QS = [{"id": "q001", "question": "ClipVault Obsidian 记忆 知识库核心",
        "expected_sources": ["MemOS"], "expected_claims": ["memory"], "risk_tags": []}]


class TestEvaluator(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
        self.manifest = export_vault(make_vault(self.tmp), os.path.join(self.tmp, "out"))
        self.export_dir = os.path.join(self.tmp, "out", "exported_vault")
        docs = baseline_search.load_docs(self.export_dir)
        self.baseline = [{"question_id": "q001", "results": baseline_search.search(_QS[0]["question"], docs)}]
        a = MockGBrainAdapter(self.export_dir); a.index()
        self.answers = [a.ask("q001", _QS[0]["question"]).to_dict()]

    def test_citation_traceability(self):
        ev = evaluate(self.answers, _QS, self.manifest, self.baseline)
        self.assertEqual(ev["metrics"]["citation_traceability"], 1.0)
        self.assertEqual(ev["metrics"]["sensitive_leakage_count"], 0)

    def test_missing_source_detected(self):
        ans = [{"question_id": "q001", "question": "x", "answer": "no cite", "citations": []}]
        ev = evaluate(ans, _QS, self.manifest, self.baseline)
        self.assertEqual(ev["metrics"]["missing_source_rate"], 1.0)

    def test_sensitive_leakage_detected(self):
        ans = [{"question_id": "q001", "question": "x", "answer": "leaked token cookie",
                "citations": [{"path": "secret/token.md"}]}]
        ev = evaluate(ans, _QS, self.manifest, self.baseline)
        self.assertGreater(ev["metrics"]["sensitive_leakage_count"], 0)

    def test_wrong_relation_detected(self):
        ans = [{"question_id": "q001", "question": "x", "answer": "a", "citations": [],
                "relations": [{"source": "A", "relation": "x", "target": "B", "evidence_path": "nope.md"}]}]
        ev = evaluate(ans, _QS, self.manifest, self.baseline)
        self.assertEqual(ev["metrics"]["wrong_relation_count"], 1)


if __name__ == "__main__":
    unittest.main()
