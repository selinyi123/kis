"""KIS-016 trial-question tests."""

import os
import shutil
import sys
import tempfile
import unittest

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(_ROOT, "src"))

from kis.gbrain_trial.questions import QUESTIONS, write_questions  # noqa: E402


class TestQuestions(unittest.TestCase):
    def test_twenty_questions_schema_valid(self):
        self.assertEqual(len(QUESTIONS), 20)
        ids = set()
        for q in QUESTIONS:
            for k in ("id", "question", "expected_sources", "expected_claims", "risk_tags"):
                self.assertIn(k, q)
            self.assertIsInstance(q["expected_sources"], list)
            self.assertIsInstance(q["risk_tags"], list)
            ids.add(q["id"])
        self.assertEqual(len(ids), 20)  # unique ids

    def test_write_questions_jsonl(self):
        tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, tmp, ignore_errors=True)
        path = write_questions(tmp)
        with open(path, encoding="utf-8") as fh:
            lines = [ln for ln in fh if ln.strip()]
        self.assertEqual(len(lines), 20)


if __name__ == "__main__":
    unittest.main()
