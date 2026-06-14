"""KIS-007 bookmark connector tests (8 cases). Pure logic + temp SQLite/vault."""

import os
import sys
import tempfile
import unittest

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(_ROOT, "src"))
sys.path.insert(0, os.path.join(_ROOT, "scripts"))

from kis.card import add_date_to_iso  # noqa: E402
from kis.classify import classify_bookmark  # noqa: E402
from kis.connectors.bookmarks import bookmark_to_card, parse_bookmarks_html  # noqa: E402
from kis.store import Store  # noqa: E402
from kis.validate import load_schema, validate_card  # noqa: E402
from ingest_bookmarks import ingest_bookmarks  # noqa: E402

SAMPLE = os.path.join(_ROOT, "examples", "bookmarks.sample.html")


class TestBookmarks(unittest.TestCase):
    def setUp(self):
        self.items = parse_bookmarks_html(SAMPLE)
        self.tmp = tempfile.mkdtemp()

    def _find(self, needle):
        return [i for i in self.items if needle in i.url]

    # 1
    def test_parse_bookmarks_extracts_links(self):
        self.assertEqual(len(self.items), 8)
        self.assertTrue(self._find("github.com"))

    # 2
    def test_parse_bookmarks_preserves_folder_path(self):
        chatgpt_ai = [i for i in self.items if "chatgpt" in i.url and i.folder_path == "AI"]
        self.assertTrue(chatgpt_ai, "expected a ChatGPT bookmark inside folder 'AI'")

    # 3
    def test_add_date_converted_to_iso(self):
        iso = add_date_to_iso("1700000000")
        self.assertTrue(iso.startswith("2023-11-14"), iso)
        self.assertTrue(iso.endswith("Z"))

    # 4
    def test_duplicate_url_deduped(self):
        dups = self._find("chatgpt.com")
        self.assertEqual(len(dups), 2)  # two raw bookmarks
        ids = {bookmark_to_card(i)["id"] for i in dups}
        self.assertEqual(len(ids), 1)  # same normalized url -> one card id

    # 5
    def test_blocked_adult_url_not_written_to_vault(self):
        vault = os.path.join(self.tmp, "vault")
        stats = ingest_bookmarks(SAMPLE, os.path.join(self.tmp, "k.db"), vault)
        self.assertGreaterEqual(stats["blocked"], 2)
        written = []
        for root, _dirs, files in os.walk(vault):
            if os.path.basename(root) == "_blocked":
                continue
            written += [os.path.join(root, f) for f in files]
        blob = ""
        for p in written:
            with open(p, encoding="utf-8") as fh:
                blob += fh.read()
        self.assertNotIn("adult-xxx.example.com", blob)
        self.assertNotIn("pqjc.example.site", blob)
        self.assertTrue(os.path.isdir(os.path.join(vault, "_blocked")))

    # 6
    def test_ai_workspace_classification(self):
        self.assertEqual(classify_bookmark("ChatGPT", "https://chatgpt.com/", "AI")["category"], "ai_workspace")
        self.assertEqual(classify_bookmark("超低价机场", "https://x.site/", "")["decision"], "blocked")

    # 7
    def test_card_schema_valid_for_bookmark(self):
        schema = load_schema()
        for item in self.items:
            if classify_bookmark(item.title, item.url, item.folder_path)["decision"] == "blocked":
                continue
            self.assertEqual(validate_card(bookmark_to_card(item), schema), [], item.url)

    # 8
    def test_ingest_bookmarks_end_to_end(self):
        db = os.path.join(self.tmp, "e2e.db")
        stats = ingest_bookmarks(SAMPLE, db, os.path.join(self.tmp, "v"))
        self.assertGreaterEqual(stats["inserted"], 5)
        self.assertGreaterEqual(stats["blocked"], 2)
        self.assertEqual(Store(db).count("web_bookmark"), stats["inserted"])


if __name__ == "__main__":
    unittest.main()
