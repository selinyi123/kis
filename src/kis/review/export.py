"""Export the review queue to markdown or JSON (KIS-014)."""

from __future__ import annotations

import json
from typing import Any


def export_queue(cards: list[dict[str, Any]], fmt: str = "md") -> str:
    if fmt == "json":
        rows = [{
            "id": c["id"],
            "status": c["lifecycle"].get("state"),
            "title": c["content"].get("title"),
            "source_type": c["source"].get("source_type"),
            "value_level": c.get("derived", {}).get("value_level"),
            "next_action": c.get("derived", {}).get("next_action"),
            "review": c.get("review"),
        } for c in cards]
        return json.dumps(rows, ensure_ascii=False, indent=2)

    lines = ["| ID | Status | Value | Next Action | Title |", "|---|---|---|---|---|"]
    for c in cards:
        d = c.get("derived", {})
        title = (c["content"].get("title") or "").replace("|", "\\|")[:60]
        lines.append(
            f"| {c['id']} | {c['lifecycle'].get('state')} | {d.get('value_level', '-')} "
            f"| {d.get('next_action', '-')} | {title} |"
        )
    return "\n".join(lines)
