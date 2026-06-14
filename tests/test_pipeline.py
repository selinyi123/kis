"""v0.1 closed-loop tests — pure logic, no network (DPMS scoring-test style).

Run:  python -m unittest discover -s tests -v
"""

import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

from kis.card import content_hash, github_star_card, infer_projects, stable_id  # noqa: E402
from kis.obsidian import render_card_md  # noqa: E402
from kis.store import Store  # noqa: E402
from kis.validate import load_schema, validate_card  # noqa: E402

_REPO = {
    "full_name": "MemTensor/MemOS",
    "html_url": "https://github.com/MemTensor/MemOS",
    "description": "Self-evolving memory OS for LLM & AI Agents",
    "language": "TypeScript",
    "stargazers_count": 9852,
    "topics": ["memory", "rag"],
    "pushed_at": "2026-06-10T00:00:00Z",
}


class TestIdentity(unittest.TestCase):
    def test_stable_id_is_deterministic(self):
        a = stable_id("github_stars", "https://github.com/x/y")
        b = stable_id("github_stars", "https://github.com/x/y")
        self.assertEqual(a, b)
        self.assertTrue(a.startswith("kc_"))

    def test_content_hash_changes_with_content(self):
        self.assertNotEqual(content_hash("t", "a"), content_hash("t", "b"))

    def test_infer_projects_maps_memory_to_kis(self):
        self.assertIn("KIS", infer_projects("a memory crawler for knowledge"))


class TestSchema(unittest.TestCase):
    def setUp(self):
        self.schema = load_schema()

    def test_sample_file_is_valid(self):
        sample_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "examples", "github-star.sample.json",
        )
        with open(sample_path, encoding="utf-8") as fh:
            card = json.load(fh)
        self.assertEqual(validate_card(card, self.schema), [])

    def test_generated_card_is_valid(self):
        card = github_star_card(_REPO)
        self.assertEqual(validate_card(card, self.schema), [])

    def test_unknown_field_rejected(self):
        card = github_star_card(_REPO)
        card["surprise"] = "boom"
        errors = validate_card(card, self.schema)
        self.assertTrue(any("unknown field" in e for e in errors))

    def test_bad_enum_rejected(self):
        card = github_star_card(_REPO)
        card["enrichment"]["evidence_level"] = "made_up"
        errors = validate_card(card, self.schema)
        self.assertTrue(any("enum" in e for e in errors))


class TestStoreIdempotency(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.db = os.path.join(self.tmp, "t.db")

    def test_upsert_is_idempotent(self):
        card = github_star_card(_REPO)
        store = Store(self.db)
        self.assertEqual(store.upsert(card), "inserted")
        self.assertEqual(store.upsert(card), "unchanged")  # re-run: no dup
        self.assertEqual(store.count(), 1)
        store.close()

    def test_content_change_is_update(self):
        store = Store(self.db)
        store.upsert(github_star_card(_REPO))
        changed = dict(_REPO, description="A brand new description")
        self.assertEqual(store.upsert(github_star_card(changed)), "updated")
        self.assertEqual(store.count(), 1)  # still one card, version bumped
        store.close()

    def test_search_finds_card(self):
        store = Store(self.db)
        store.upsert(github_star_card(_REPO))
        hits = store.search("memory")
        self.assertTrue(any(h["content"]["title"] == "MemTensor/MemOS" for h in hits))
        store.close()


class TestObsidian(unittest.TestCase):
    def test_render_has_frontmatter_and_link(self):
        md = render_card_md(github_star_card(_REPO))
        self.assertTrue(md.startswith("---"))
        self.assertIn("kis_id: kc_", md)
        self.assertIn("[[KIS]]", md)


if __name__ == "__main__":
    unittest.main()
