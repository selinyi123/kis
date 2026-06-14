"""Deterministic project-relevance scoring (KIS-013a).

Returns a 0.0-1.0 relevance per active project, by keyword hits in the card's
text. No LLM, no network. Keys match schema derived.project_relevance.
"""

from __future__ import annotations

from typing import Any

PROJECT_KEYWORDS: dict[str, tuple[str, ...]] = {
    "kis": ("knowledge", "memory", "crawler", "rag", "search", "知识", "记忆", "爬虫",
            "codegraph", "memos", "gbrain", "catalog", "agent memory"),
    "clipvault": ("clipboard", "剪切板", "obsidian", "ime", "android", "sync", "note", "笔记"),
    "dpms": ("lottery", "抽奖", "playwright", "anti-bot", "captcha", "automation", "account", "养号"),
    "prompt_engine": ("prompt", "llm", "evaluation", "评测", "optimize", "optimization", "skill", "rubric"),
    "visual_prompt_library": ("image", "3d", "midjourney", "绘画", "visual", "design", "style",
                              "tripo", "rodin", "gallery", "prompt gallery"),
    "trading_research": ("quant", "trading", "polymarket", "量化", "交易", "finance", "market", "预测市场"),
}

_HIT_WEIGHT = 0.34  # ~3 hits -> 1.0


def _haystack(card: dict[str, Any]) -> str:
    c, s, e = card["content"], card["source"], card["enrichment"]
    parts = [
        c.get("title", ""), c.get("description", ""), c.get("text_preview", ""),
        s.get("url", ""), e.get("category", ""), " ".join(e.get("tags", [])),
    ]
    return " ".join(parts).lower()


def compute_project_relevance(card: dict[str, Any]) -> dict[str, float]:
    hay = _haystack(card)
    out: dict[str, float] = {}
    for project, kws in PROJECT_KEYWORDS.items():
        hits = sum(1 for k in kws if k.lower() in hay)
        out[project] = round(min(hits * _HIT_WEIGHT, 1.0), 3)
    return out
