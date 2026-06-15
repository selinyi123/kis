"""KIS-014 CLI tests — list/show/approve/archive/defer/reject, dry-run, filters."""

import os
import shutil
import sys
import tempfile
import unittest

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(_ROOT, "src"))
sys.path.insert(0, os.path.join(_ROOT, "scripts"))

from kis.card import github_star_card  # noqa: E402
from kis.enrich.heuristic import enrich_card  # noqa: E402
from kis.store import Store  # noqa: E402
import review_cards as rc  # noqa: E402

_REPO = {"full_name": "MemTensor/MemOS", "html_url": "https://github.com/MemTensor/MemOS",
         "description": "memory agent rag", "language": "TS", "stargazers_count": 9, "topics": ["memory", "rag"]}


class TestReviewCli(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
        self.db = os.path.join(self.tmp, "k.db")
        self.vault = os.path.join(self.tmp, "v")
        s = Store(self.db)
        self.card = enrich_card(github_star_card(_REPO))
        s.upsert(self.card)
        s.close()
        self.parser = rc.build_parser()

    def _run(self, argv):
        args = self.parser.parse_args(["--db-path", self.db, "--obsidian-dir", self.vault, *argv])
        store = Store(self.db)
        try:
            if args.command == "list":
                return rc.cmd_list(store, args)
            if args.command == "show":
                return rc.cmd_show(store, args)
            if args.command == "export":
                return rc.cmd_export(store, args)
            from kis.validate import load_schema
            return rc.cmd_write(store, args, load_schema())
        finally:
            store.close()

    def _status(self):
        return Store(self.db).get_card(self.card["id"])["lifecycle"]["state"]

    def test_list_and_show_and_export(self):
        self.assertEqual(self._run(["list", "--status", "inbox"]), 0)
        self.assertEqual(self._run(["show", "--card-id", self.card["id"]]), 0)
        self.assertEqual(self._run(["export", "--status", "inbox", "--format", "json"]), 0)

    def test_dry_run_does_not_mutate(self):
        self._run(["mark-reviewed", "--card-id", self.card["id"], "--reason", "r", "--dry-run"])
        self.assertEqual(self._status(), "inbox")  # unchanged

    def test_approve_requires_reviewed_first(self):
        # inbox -> approve is illegal; CLI returns 1 and leaves status inbox
        self.assertEqual(self._run(["approve", "--card-id", self.card["id"], "--reason", "x"]), 1)
        self.assertEqual(self._status(), "inbox")

    def test_full_review_then_approve(self):
        self.assertEqual(self._run(["mark-reviewed", "--card-id", self.card["id"], "--reason", "verified"]), 0)
        self.assertEqual(self._status(), "reviewed")
        self.assertEqual(self._run(["approve", "--card-id", self.card["id"], "--reason", "promote"]), 0)
        self.assertEqual(self._status(), "canonical")

    def test_archive_defer_reject_paths(self):
        for cmd, expect in (("archive", "archived"), ("defer", "deferred"), ("reject", "rejected")):
            s = Store(self.db); c = enrich_card(github_star_card({**_REPO, "full_name": f"a/{cmd}",
                              "html_url": f"https://github.com/a/{cmd}"})); s.upsert(c); s.close()
            self.assertEqual(self._run([cmd, "--card-id", c["id"], "--reason", "because"]), 0)
            self.assertEqual(Store(self.db).get_card(c["id"])["lifecycle"]["state"], expect)

    def test_idempotent_cli(self):
        self._run(["mark-reviewed", "--card-id", self.card["id"], "--reason", "v"])
        self.assertEqual(self._run(["mark-reviewed", "--card-id", self.card["id"], "--reason", "v"]), 0)  # no-op
        self.assertEqual(self._status(), "reviewed")

    def test_reason_is_required_by_argparse(self):
        with self.assertRaises(SystemExit):
            self.parser.parse_args(["approve", "--card-id", "x"])  # missing --reason


if __name__ == "__main__":
    unittest.main()
