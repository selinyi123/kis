"""KIS-013 enrich CLI / pipeline tests (offline, temp db, cleaned up)."""

import os
import shutil
import sys
import tempfile
import unittest

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(_ROOT, "src"))
sys.path.insert(0, os.path.join(_ROOT, "scripts"))

from kis.card import github_star_card  # noqa: E402
from kis.store import Store  # noqa: E402
from enrich_cards import enrich_db  # noqa: E402

_REPOS = [
    {"full_name": "MemTensor/MemOS", "html_url": "https://github.com/MemTensor/MemOS",
     "description": "Self-evolving memory OS for LLM agents", "language": "TS", "stargazers_count": 9, "topics": ["memory"]},
    {"full_name": "a/b", "html_url": "https://github.com/a/b", "description": "a tool",
     "language": "Go", "stargazers_count": 2, "topics": []},
]


class TestEnrichCli(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
        self.db = os.path.join(self.tmp, "k.db")
        s = Store(self.db)
        for r in _REPOS:
            s.upsert(github_star_card(r))
        s.close()

    def test_cli_dry_run_does_not_mutate_db(self):
        stats = enrich_db(self.db, None, mode="heuristic", dry_run=True)
        self.assertTrue(stats["dry_run"])
        self.assertEqual(stats["updated"], 0)
        # no card got a derived layer persisted
        self.assertTrue(all("derived" not in c for c in Store(self.db).all_cards()))

    def test_enrich_end_to_end_heuristic(self):
        vault = os.path.join(self.tmp, "v")
        stats = enrich_db(self.db, vault, mode="heuristic")
        self.assertEqual(stats["processed"], len(_REPOS))
        self.assertEqual(stats["updated"], len(_REPOS))
        self.assertEqual(stats["errors"], 0)
        cards = Store(self.db).all_cards()
        self.assertTrue(all("derived" in c for c in cards))
        self.assertTrue(all(c["derived"]["processing_status"] == "heuristic" for c in cards))
        # idempotent: second run skips already-done cards
        stats2 = enrich_db(self.db, vault, mode="heuristic")
        self.assertEqual(stats2["skipped_done"], len(_REPOS))
        self.assertEqual(stats2["updated"], 0)


if __name__ == "__main__":
    unittest.main()
