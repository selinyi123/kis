"""Apply a human review decision to a card (KIS-014). Pure: returns a new card."""

from __future__ import annotations

import copy
from typing import Any

from ..card import now_iso
from . import models
from .policy import DECISION_TO_STATUS, IllegalTransition, assert_review_only, is_legal


class ReviewError(ValueError):
    """Raised for invalid review requests (blocked card, empty reason, etc.)."""


def apply_review(card: dict[str, Any], decision: str, reason: str,
                 reviewer: str = "human", reviewed_at: str | None = None) -> tuple[dict[str, Any], bool]:
    """Return (new_card, changed).

    changed=False means the card was already in the target status (idempotent
    no-op). Raises ReviewError / IllegalTransition on invalid requests. Writes
    ONLY lifecycle + review; immutability of the factual core is asserted.
    """
    if card["safety"].get("sensitivity") == "blocked":
        raise ReviewError("blocked cards cannot enter the review queue")
    if not reason or not reason.strip():
        raise ReviewError("review reason must not be empty")
    if decision not in DECISION_TO_STATUS:
        raise ReviewError(f"unknown decision: {decision}")

    frm = card["lifecycle"]["state"]
    to = DECISION_TO_STATUS[decision]

    if frm == to:
        return card, False  # idempotent: already in target status

    if not is_legal(frm, to):
        raise IllegalTransition(f"transition not allowed: {frm} -> {to} (decision={decision})")

    out = copy.deepcopy(card)
    ts = reviewed_at or now_iso()
    sh = models.source_hash(card)
    dh = models.derived_hash(card)
    rh = models.review_hash(
        card_id=card["id"], previous_status=frm, next_status=to, decision=decision,
        reason=reason.strip(), reviewer=reviewer, reviewed_at=ts, source_hash=sh, derived_hash=dh,
    )
    out["lifecycle"]["state"] = to
    out["lifecycle"]["updated_at"] = ts
    out["lifecycle"]["version"] = int(card["lifecycle"]["version"]) + 1
    out["review"] = {
        "decision": decision, "reason": reason.strip(), "reviewer": reviewer,
        "reviewed_at": ts, "previous_status": frm, "next_status": to,
        "source_hash": sh, "derived_hash": dh, "review_hash": rh,
    }
    assert_review_only(card, out)  # factual core untouched
    return out, True
