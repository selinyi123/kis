"""KIS-016 report tests."""

import os
import sys
import unittest

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(_ROOT, "src"))

from kis.gbrain_trial.report import decide, render_report  # noqa: E402

_EV = {"metrics": {"citation_traceability": 1.0, "missing_source_rate": 0.0,
                   "unknown_when_no_source_rate": 1.0, "sensitive_leakage_count": 0,
                   "wrong_relation_count": 0, "conflict_detection_count": 0,
                   "stale_warning_count": 0, "baseline_overlap": 0.5,
                   "answer_usefulness_score": 0.8},
       "relation_audit": [], "leakage_audit": []}
_MANIFEST = {"source_vault": "v", "summary": {"included_count": 6, "denied_count": 7, "total_bytes": 100},
             "denied_files": [{"source_path": "secret/x.md", "reason": "deny pattern: secret"}]}


class TestReport(unittest.TestCase):
    def test_report_has_all_sections(self):
        md = render_report(_MANIFEST, [{"id": "q001"}], _EV, "mock", False, [])
        for sec in ("# KIS-016 GBrain Read-Only Trial Report", "## Summary", "## Export Scope",
                    "## Denied Files", "## Questions", "## Baseline vs GBrain", "## Citation Traceability",
                    "## Entity Relation Audit", "## Sensitive Leakage Audit", "## Failures", "## Decision"):
            self.assertIn(sec, md)

    def test_decision_keeps_readonly_and_blocks_writeback(self):
        d = decide(_EV["metrics"])
        self.assertEqual(d["keep_readonly"], "yes")
        self.assertEqual(d["allow_writeback"], "no")
        self.assertEqual(d["allow_canonical"], "no")
        self.assertEqual(d["promote_to_kis017"], "yes")  # clean metrics

    def test_decision_no_promote_on_leakage(self):
        bad = dict(_EV["metrics"], sensitive_leakage_count=1)
        self.assertEqual(decide(bad)["promote_to_kis017"], "no")


if __name__ == "__main__":
    unittest.main()
