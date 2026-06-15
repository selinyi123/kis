"""Lifecycle transition policy (KIS-014). Pure, deterministic, no I/O."""

from __future__ import annotations

# Legal lifecycle transitions. Anything not listed is rejected.
# canonical/archived/rejected are terminal (no auto downgrade); canonical is
# only ever reached from `reviewed` via an explicit human approve.
LEGAL: dict[str, set[str]] = {
    "inbox": {"reviewed", "archived", "deferred", "rejected"},
    "reviewed": {"canonical", "archived", "deferred", "rejected"},
    "deferred": {"inbox", "reviewed", "archived", "rejected"},
    "canonical": set(),
    "archived": set(),
    "rejected": set(),
}

# decision -> resulting lifecycle status
DECISION_TO_STATUS: dict[str, str] = {
    "reviewed": "reviewed",
    "approve_canonical": "canonical",
    "archive": "archived",
    "defer": "deferred",
    "reject": "rejected",
}

# CLI command -> decision
COMMAND_TO_DECISION: dict[str, str] = {
    "mark-reviewed": "reviewed",
    "approve": "approve_canonical",
    "archive": "archive",
    "defer": "defer",
    "reject": "reject",
}


class IllegalTransition(ValueError):
    """Raised when a lifecycle transition is not permitted."""


def next_status_for(decision: str) -> str:
    if decision not in DECISION_TO_STATUS:
        raise IllegalTransition(f"unknown decision: {decision}")
    return DECISION_TO_STATUS[decision]


def is_legal(from_status: str, to_status: str) -> bool:
    return to_status in LEGAL.get(from_status, set())


# Fields the review gate may NEVER modify (the factual / provenance core).
LOCKED_FIELDS = ("source", "content", "enrichment", "linkage", "safety", "derived")


def assert_review_only(before: dict, after: dict) -> None:
    """Raise if review changed anything other than lifecycle/review."""
    for key in LOCKED_FIELDS:
        if before.get(key) != after.get(key):
            raise ValueError(f"review illegally modified locked field '{key}'")
