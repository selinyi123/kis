"""Dedupe for external ingestion (KIS-018).

Three keys: normalized_url, content_hash, (source_type, source_id). Plus a
store check so re-importing an already-stored item is skipped_duplicate.
Read-only against the store, so dry-run and real runs report identical counts.
"""

from __future__ import annotations

from typing import Any


class Deduper:
    def __init__(self, store: Any = None):
        self.store = store
        self._urls: set[str] = set()
        self._hashes: set[str] = set()
        self._srcids: set[tuple[str, str]] = set()

    def status(self, card: dict[str, Any]) -> str:
        """Return 'new' or 'duplicate'. Marks the card as seen when new."""
        src = card["source"]
        nu = src.get("normalized_url") or src.get("url", "")
        ch = card["content_hash"]
        sid = (src.get("source_type", ""), src.get("source_id", ""))

        if nu in self._urls or ch in self._hashes or sid in self._srcids:
            return "duplicate"
        if self.store is not None:
            existing = self.store.get(card["id"])
            if existing is not None and existing.get("content_hash") == ch:
                return "duplicate"

        self._urls.add(nu)
        self._hashes.add(ch)
        self._srcids.add(sid)
        return "new"
