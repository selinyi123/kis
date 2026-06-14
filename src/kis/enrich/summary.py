"""Deterministic heuristic summary (KIS-013a). Never empty for a valid card."""

from __future__ import annotations

import re
from typing import Any

_SENT = re.compile(r"[.!?。！？]\s")


def _first_sentence(text: str, limit: int = 220) -> str:
    text = re.sub(r"\s+", " ", (text or "")).strip()
    if not text:
        return ""
    parts = _SENT.split(text)
    first = parts[0].strip() if parts else text
    return (first[:limit]).strip()


def heuristic_summary(card: dict[str, Any]) -> str:
    c, e, s = card["content"], card["enrichment"], card["source"]
    title = (c.get("title") or s.get("url") or "Untitled").strip()
    detail = _first_sentence(c.get("description") or "") or _first_sentence(c.get("text_preview") or "")
    category = e.get("category") or s.get("source_type", "")
    if detail:
        return f"{title} — {detail} [{category}]"
    return f"{title} [{category}]"
