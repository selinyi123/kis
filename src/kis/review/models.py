"""Review provenance hashing (KIS-014). Pure, deterministic."""

from __future__ import annotations

import hashlib
import json
from typing import Any


def source_hash(card: dict[str, Any]) -> str:
    """Snapshot hash of the factual source — the card's content fingerprint."""
    return card.get("content_hash", "")


def derived_hash(card: dict[str, Any]) -> str:
    d = card.get("derived")
    if not d:
        return "none"
    payload = json.dumps(d, ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


def review_hash(*, card_id: str, previous_status: str, next_status: str, decision: str,
                reason: str, reviewer: str, reviewed_at: str,
                source_hash: str, derived_hash: str) -> str:
    """Deterministic hash over the full decision payload (audit fingerprint)."""
    payload = json.dumps({
        "card_id": card_id, "previous_status": previous_status, "next_status": next_status,
        "decision": decision, "reason": reason, "reviewer": reviewer,
        "reviewed_at": reviewed_at, "source_hash": source_hash, "derived_hash": derived_hash,
    }, ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]
