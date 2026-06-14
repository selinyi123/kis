"""Deterministic value scoring + next-action selection (KIS-013a).

value_score is a 0.0-1.0 float (distinct from the source-level
enrichment.value_score). No LLM, no network — fully reproducible.
"""

from __future__ import annotations

from typing import Any

_HIGH_VALUE_CATEGORIES = {"agent_tools", "ai_workspace", "dev_resources"}
_UNCERTAIN_CATEGORIES = {"trading_research", "ops_tools", "general"}
_BASE = 0.40
_RELEVANT_THRESHOLD = 0.34


def _clamp01(x: float) -> float:
    return round(max(0.0, min(1.0, x)), 3)


def compute_value_score(card: dict[str, Any], relevance: dict[str, float]) -> tuple[float, list[str]]:
    """Return (score, reason_tags). Weighted additive signals over a base."""
    e, c, s, saf = card["enrichment"], card["content"], card["source"], card["safety"]
    tags: list[str] = []
    score = _BASE

    if max(relevance.values(), default=0.0) >= _RELEVANT_THRESHOLD:
        score += 0.25
        tags.append("project_relevant")
    if e.get("category") in _HIGH_VALUE_CATEGORIES:
        score += 0.15
        tags.append("category_high_value")
    if c.get("clean_markdown") or c.get("text_preview"):
        score += 0.10
        tags.append("has_extracted_text")
    if len((c.get("description") or "")) >= 60:
        score += 0.10
        tags.append("info_dense")
    if s.get("source_type") == "github_star" and (e.get("topics") or e.get("summary")):
        score += 0.10
        tags.append("github_tech_direction")
    if e.get("category") in _UNCERTAIN_CATEGORIES:
        score -= 0.05
        tags.append("uncertain_category")
    if saf.get("sensitivity") == "internal":
        score -= 0.10
        tags.append("sensitive_internal")

    return _clamp01(score), tags


def value_level(score: float) -> str:
    if score >= 0.85:
        return "critical"
    if score >= 0.65:
        return "hot"
    if score >= 0.40:
        return "warm"
    return "cold"


def next_action(card: dict[str, Any], relevance: dict[str, float]) -> str:
    e, saf, c = card["enrichment"], card["safety"], card["content"]
    category = e.get("category", "")
    hay = f"{c.get('title','')} {c.get('description','')} {' '.join(e.get('tags', []))}".lower()

    if saf.get("sensitivity") in {"internal", "blocked"}:
        return "ignore"
    memory_signals = ("gbrain", "memos", "crawl4ai", "agent", "knowledge", "memory", "rag", "codegraph")
    if relevance.get("kis", 0) >= 0.34 or category in {"agent_tools", "ai_workspace"} \
            or any(k in hay for k in memory_signals):
        return "integrate"
    if category == "visual_tools" or "prompt" in hay or "gallery" in hay or relevance.get("visual_prompt_library", 0) >= 0.34:
        return "test"
    if category in {"dev_resources", "research"}:
        return "read"
    if "news" in hay or "资讯" in hay or "insider" in hay:
        return "monitor"
    return "archive"


def review_flags(card: dict[str, Any], score: float) -> list[str]:
    flags = ["summary_unreviewed"]  # derived summary always needs a human glance
    if 0.40 <= score < 0.65:
        flags.append("low_confidence")
    if card["safety"].get("sensitivity") == "internal":
        flags.append("sensitive_internal")
    if card["enrichment"].get("category") == "general":
        flags.append("uncertain_category")
    if not (card["content"].get("description") or card["content"].get("text_preview")):
        flags.append("thin_content")
    return flags
