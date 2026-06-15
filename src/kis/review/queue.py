"""Review queue filtering (KIS-014). Pure helpers over a list of cards."""

from __future__ import annotations

from typing import Any, Iterable


def filter_cards(
    cards: Iterable[dict[str, Any]],
    *,
    status: str | None = None,
    value_level: str | None = None,
    next_action: str | None = None,
    source_type: str | None = None,
    category: str | None = None,
    exclude_blocked: bool = True,
) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for c in cards:
        if exclude_blocked and c["safety"].get("sensitivity") == "blocked":
            continue
        if status and c["lifecycle"].get("state") != status:
            continue
        derived = c.get("derived", {})
        if value_level and derived.get("value_level") != value_level:
            continue
        if next_action and derived.get("next_action") != next_action:
            continue
        if source_type and c["source"].get("source_type") != source_type:
            continue
        if category and c["enrichment"].get("category") != category:
            continue
        out.append(c)
    return out


def queue_counts(cards: Iterable[dict[str, Any]]) -> dict[str, int]:
    """Count cards per lifecycle status (blocked excluded — they aren't queued)."""
    counts = {s: 0 for s in ("inbox", "reviewed", "canonical", "archived", "deferred", "rejected")}
    for c in cards:
        if c["safety"].get("sensitivity") == "blocked":
            continue
        st = c["lifecycle"].get("state")
        if st in counts:
            counts[st] += 1
    return counts
