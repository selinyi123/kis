"""Offline baseline search over the exported snapshot (KIS-016).

Plain keyword/term overlap (incl. CJK bigrams) — the control GBrain must beat.
No GBrain, no network.
"""

from __future__ import annotations

import os
import re
from typing import Any

_WORD = re.compile(r"[a-z0-9]{2,}")
_CJK = re.compile(r"[一-鿿]")


def tokens(text: str) -> set[str]:
    text = (text or "").lower()
    words = set(_WORD.findall(text))
    cjk = _CJK.findall(text)
    bigrams = {cjk[i] + cjk[i + 1] for i in range(len(cjk) - 1)}
    return words | bigrams


def load_docs(export_dir: str) -> list[tuple[str, str]]:
    """Return [(rel_path, text)] for .md/.txt under the exported snapshot."""
    docs: list[tuple[str, str]] = []
    if not os.path.isdir(export_dir):
        return docs
    for root, _dirs, files in os.walk(export_dir):
        for name in files:
            if not name.lower().endswith((".md", ".txt")):
                continue
            p = os.path.join(root, name)
            try:
                with open(p, encoding="utf-8", errors="replace") as fh:
                    docs.append((os.path.relpath(p, export_dir).replace("\\", "/"), fh.read()))
            except OSError:
                continue
    return docs


def search(question: str, docs: list[tuple[str, str]], top_k: int = 3) -> list[dict[str, Any]]:
    q = tokens(question)
    if not q:
        return []
    scored = []
    for path, text in docs:
        inter = q & tokens(text)
        if inter:
            scored.append((path, round(len(inter) / len(q), 3), _snippet(text, inter)))
    scored.sort(key=lambda r: (-r[1], r[0]))
    return [{"path": p, "score": s, "snippet": snip} for p, s, snip in scored[:top_k]]


def _snippet(text: str, terms: set[str], width: int = 160) -> str:
    flat = re.sub(r"\s+", " ", text).strip()
    low = flat.lower()
    for t in sorted(terms, key=len, reverse=True):
        i = low.find(t)
        if i >= 0:
            start = max(0, i - 40)
            return flat[start:start + width].strip()
    return flat[:width].strip()
