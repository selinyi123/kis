"""Review statistics (KIS-015). Pure: counters over a card list."""

from __future__ import annotations

from collections import Counter
from typing import Any

_PROJECTS = ("kis", "clipvault", "dpms", "prompt_engine", "visual_prompt_library", "trading_research")
_RELEVANT = 0.34


def compute_review_stats(cards: list[dict[str, Any]]) -> dict[str, dict[str, int]]:
    cards = [c for c in cards if c["safety"].get("sensitivity") != "blocked"]
    by_lifecycle: Counter = Counter()
    by_source_type: Counter = Counter()
    by_category: Counter = Counter()
    by_value_level: Counter = Counter()
    by_next_action: Counter = Counter()
    by_sensitivity: Counter = Counter()
    by_generated_day: Counter = Counter()
    by_project: Counter = Counter()

    for c in cards:
        d = c.get("derived", {})
        by_lifecycle[c["lifecycle"].get("state", "inbox")] += 1
        by_source_type[c["source"].get("source_type", "unknown")] += 1
        by_category[c["enrichment"].get("category") or "unknown"] += 1
        by_value_level[d.get("value_level", "unknown")] += 1
        by_next_action[d.get("next_action", "unknown")] += 1
        by_sensitivity[c["safety"].get("sensitivity", "public")] += 1
        gen_at = d.get("generated_at") or ""
        by_generated_day[gen_at[:10] or "unknown"] += 1
        rel = d.get("project_relevance", {})
        for p in _PROJECTS:
            if rel.get(p, 0) >= _RELEVANT:
                by_project[p] += 1

    # External Inbox (KIS-018): inbox cards by source_type and by project.
    inbox = [c for c in cards if c["lifecycle"].get("state") == "inbox"]
    ext_src: Counter = Counter(c["source"].get("source_type", "unknown") for c in inbox)
    ext_proj: Counter = Counter((c["linkage"].get("projects") or ["(none)"])[0] for c in inbox)

    return {
        "by_lifecycle": dict(by_lifecycle),
        "by_source_type": dict(by_source_type),
        "by_category": dict(by_category),
        "by_value_level": dict(by_value_level),
        "by_next_action": dict(by_next_action),
        "by_sensitivity": dict(by_sensitivity),
        "by_generated_day": dict(by_generated_day),
        "by_project_relevance": dict(by_project),
        "external_inbox": {
            "total": len(inbox),
            "by_source_type": dict(ext_src),
            "by_project": dict(ext_proj),
        },
        "total": len(cards),
    }
