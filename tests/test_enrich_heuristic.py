"""KIS-013a heuristic enrichment tests (deterministic, offline)."""

import os
import sys
import unittest

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(_ROOT, "src"))

from kis.card import github_star_card  # noqa: E402
from kis.connectors.bookmarks import BookmarkItem, bookmark_to_card  # noqa: E402
from kis.enrich.heuristic import build_derived, enrich_card  # noqa: E402
from kis.enrich.project_relevance import compute_project_relevance  # noqa: E402
from kis.enrich.scoring import next_action, value_level  # noqa: E402
from kis.enrich.summary import heuristic_summary  # noqa: E402

_MEM_REPO = {"full_name": "MemTensor/MemOS", "html_url": "https://github.com/MemTensor/MemOS",
             "description": "Self-evolving memory OS for LLM & AI Agents: hybrid retrieval and RAG",
             "language": "TypeScript", "stargazers_count": 9852, "topics": ["memory", "rag", "agent"]}
_PROMPT_REPO = {"full_name": "x/prompt-eval", "html_url": "https://github.com/x/prompt-eval",
                "description": "Prompt optimization and LLM evaluation rubric with skill scoring",
                "language": "Python", "stargazers_count": 10, "topics": ["prompt", "llm", "evaluation"]}


def _visual_card():
    return bookmark_to_card(BookmarkItem(title="Tripo Studio 3D", url="https://tripo3d.ai/", folder_path="", add_date="1700000000"))


class TestHeuristic(unittest.TestCase):
    def test_heuristic_summary_never_empty_for_valid_card(self):
        for card in (github_star_card(_MEM_REPO), _visual_card()):
            self.assertTrue(heuristic_summary(card).strip())

    def test_value_score_range_0_to_1(self):
        for card in (github_star_card(_MEM_REPO), _visual_card(), github_star_card(_PROMPT_REPO)):
            d = build_derived(card)
            self.assertGreaterEqual(d["value_score"], 0.0)
            self.assertLessEqual(d["value_score"], 1.0)

    def test_value_level_thresholds(self):
        self.assertEqual(value_level(0.9), "critical")
        self.assertEqual(value_level(0.7), "hot")
        self.assertEqual(value_level(0.5), "warm")
        self.assertEqual(value_level(0.1), "cold")

    def test_project_relevance_detects_kis(self):
        rel = compute_project_relevance(github_star_card(_MEM_REPO))
        self.assertGreater(rel["kis"], 0.0)

    def test_project_relevance_detects_prompt_engine(self):
        rel = compute_project_relevance(github_star_card(_PROMPT_REPO))
        self.assertGreater(rel["prompt_engine"], 0.0)

    def test_next_action_integrate_for_memory_system(self):
        card = github_star_card(_MEM_REPO)
        self.assertEqual(next_action(card, compute_project_relevance(card)), "integrate")

    def test_next_action_test_for_visual_tool(self):
        card = _visual_card()
        self.assertEqual(next_action(card, compute_project_relevance(card)), "test")

    def test_blocked_cards_not_enriched(self):
        card = github_star_card(_MEM_REPO)
        card["safety"]["sensitivity"] = "blocked"
        self.assertIsNone(enrich_card(card))

    def test_enrichment_only_writes_derived_fields(self):
        card = github_star_card(_MEM_REPO)
        before = {k: card[k] for k in ("source", "content", "enrichment", "linkage", "lifecycle", "safety")}
        out = enrich_card(card)
        self.assertIn("derived", out)
        for k, v in before.items():
            self.assertEqual(out[k], v)  # source/provenance untouched
        self.assertIn("input_hash", out["derived"]["generator"])


if __name__ == "__main__":
    unittest.main()
