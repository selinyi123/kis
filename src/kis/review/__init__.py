"""KIS-014 Human Review Gate.

Turns derived (model opinion) into a human-confirmed lifecycle:

    inbox ──┬─▶ reviewed ──┬─▶ canonical   (explicit human approve ONLY)
            │              ├─▶ archived
            │              ├─▶ deferred
            │              └─▶ rejected
            ├─▶ archived / deferred / rejected
    deferred ─▶ inbox / reviewed / archived / rejected

Hard rules (see docs/KIS-014_LIFECYCLE_POLICY.md):
  * AI/derived NEVER auto-promotes to canonical.
  * Review writes ONLY lifecycle + review (source/content/enrichment/linkage/
    safety/derived are immutable — assert_review_only enforces it).
  * Every decision is audited: previous/next status, decision, reason, reviewer,
    reviewed_at, source_hash, derived_hash, review_hash.
  * blocked cards never enter the queue.
"""

from .actions import ReviewError, apply_review
from .policy import COMMAND_TO_DECISION, IllegalTransition, is_legal, next_status_for

__all__ = ["apply_review", "ReviewError", "IllegalTransition", "is_legal",
           "next_status_for", "COMMAND_TO_DECISION"]
