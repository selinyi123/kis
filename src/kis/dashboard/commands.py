"""Suggested CLI command generation (KIS-015).

Commands are copy-paste SUGGESTIONS only. The Inbox page NEVER suggests
approve/canonical — canonical comes only from `reviewed` via the human gate.
Every command carries --card-id and --reason.
"""

from __future__ import annotations

from typing import Any

_SCRIPT = "python scripts/review_cards.py"


def _cmd(action: str, card_id: str, reason: str) -> str:
    return f'{_SCRIPT} {action} --card-id {card_id} --reason "{reason}"'


def inbox_commands(card: dict[str, Any]) -> list[str]:
    cid = card["id"]
    # NOTE: no approve here — inbox cannot go canonical.
    return [
        _cmd("mark-reviewed", cid, "verified source and relevance"),
        _cmd("defer", cid, "revisit later"),
        _cmd("archive", cid, "low relevance after review"),
    ]


def canonical_commands(card: dict[str, Any]) -> list[str]:
    return [_cmd("approve", card["id"], "human approved after review")]


def archive_commands(card: dict[str, Any]) -> list[str]:
    return [_cmd("archive", card["id"], "archive low-value / stale card")]


def deferred_commands(card: dict[str, Any]) -> list[str]:
    cid = card["id"]
    return [
        _cmd("mark-reviewed", cid, "reviewed after deferral"),
        _cmd("archive", cid, "archived after deferral"),
    ]


def rejected_commands(card: dict[str, Any]) -> list[str]:
    # Audit-only view — intentionally no approve/restore commands.
    return []
