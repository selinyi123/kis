"""Pure card selectors + sorting for the review dashboard (KIS-015)."""

from __future__ import annotations

from typing import Any

from .models import ACTION_RANK, VALUE_RANK, _UNKNOWN_RANK


def _state(c: dict[str, Any]) -> str:
    return c["lifecycle"].get("state", "inbox")


def _blocked(c: dict[str, Any]) -> bool:
    return c["safety"].get("sensitivity") == "blocked"


def _vl(c: dict[str, Any]) -> str | None:
    return c.get("derived", {}).get("value_level")


def _na(c: dict[str, Any]) -> str | None:
    return c.get("derived", {}).get("next_action")


def select_inbox_cards(cards: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sort_review_cards([c for c in cards if not _blocked(c) and _state(c) == "inbox"])


def select_canonical_candidates(cards: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """ONLY reviewed + (critical|hot) + (integrate|test). Never inbox."""
    out = [c for c in cards if not _blocked(c) and _state(c) == "reviewed"
           and _vl(c) in {"critical", "hot"} and _na(c) in {"integrate", "test"}]
    return sort_review_cards(out)


def select_archive_candidates(cards: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """next_action==archive OR value_level==cold OR state==rejected.
    Never canonical (no reverse transition this phase); already-archived excluded."""
    out = []
    for c in cards:
        if _blocked(c) or _state(c) in {"canonical", "archived"}:
            continue
        if _na(c) == "archive" or _vl(c) == "cold" or _state(c) == "rejected":
            out.append(c)
    return sort_review_cards(out)


def select_deferred_cards(cards: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sort_review_cards([c for c in cards if not _blocked(c) and _state(c) == "deferred"])


def select_rejected_cards(cards: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sort_review_cards([c for c in cards if not _blocked(c) and _state(c) == "rejected"])


def sort_review_cards(cards: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """critical>hot>warm>cold, then integrate>test>read>monitor>archive>ignore,
    then newer first. Stable."""
    by_new = sorted(cards, key=lambda c: c["lifecycle"].get("created_at", ""), reverse=True)
    return sorted(by_new, key=lambda c: (
        VALUE_RANK.get(_vl(c), _UNKNOWN_RANK),
        ACTION_RANK.get(_na(c), _UNKNOWN_RANK),
    ))
