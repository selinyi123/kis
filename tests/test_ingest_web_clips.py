"""KIS-018 web-clip ingest tests."""

import os
import shutil
import sys
import tempfile
import unittest

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(_ROOT, "src"))

from kis.ingest import runner  # noqa: E402
from kis.store import Store  # noqa: E402

_FIX = os.path.join(_ROOT, "tests", "fixtures", "web_clips.jsonl")


class TestIngestWebClips(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
        self.db = os.path.join(self.tmp, "k.db")

    def test_import_counts(self):
        store = Store(self.db)
        rep = runner.ingest("web-clips", _FIX, store, os.path.join(self.tmp, "v"))
        self.assertEqual(rep.total_seen, 5)
        self.assertEqual(rep.created, 1)            # article a
        self.assertEqual(rep.skipped_duplicate, 1)  # a dup
        self.assertEqual(rep.blocked, 1)            # sk-... secret
        self.assertEqual(rep.errors, 2)             # missing url + malformed line
        self.assertEqual(Store(self.db).count("web_clip"), 1)

    def test_empty_input_ok(self):
        empty = os.path.join(self.tmp, "empty.jsonl")
        open(empty, "w").close()
        rep = runner.ingest("web-clips", empty, Store(self.db), None)
        self.assertEqual(rep.total_seen, 0)
        self.assertEqual(rep.created, 0)


if __name__ == "__main__":
    unittest.main()
