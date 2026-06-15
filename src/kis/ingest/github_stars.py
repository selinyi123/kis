"""Parse a GitHub Stars snapshot export into repo dicts (KIS-018). No network."""

from __future__ import annotations

import json
import re
from typing import Any

_REPO_RE = re.compile(r"([A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+)")


def _to_repo(d: dict[str, Any]) -> dict[str, Any]:
    full = d.get("full_name") or d.get("source_id") or d.get("repo") or d.get("name") or ""
    return {
        "full_name": full,
        "html_url": d.get("html_url") or d.get("url") or (f"https://github.com/{full}" if full else ""),
        "description": d.get("description") or d.get("summary"),
        "language": d.get("language"),
        "stargazers_count": d.get("stargazers_count") if d.get("stargazers_count") is not None else d.get("stars_count"),
        "topics": d.get("topics") or [],
        "pushed_at": d.get("pushed_at") or d.get("updated_at"),
    }


def parse(path: str) -> list[dict[str, Any]]:
    with open(path, encoding="utf-8") as fh:
        text = fh.read()
    if path.lower().endswith(".md"):
        return [_to_repo({"full_name": m}) for m in dict.fromkeys(_REPO_RE.findall(text))]
    data = json.loads(text)
    if isinstance(data, dict):
        data = data.get("repos") or data.get("items") or data.get("stars") or []
    return [_to_repo(item.get("repo", item) if isinstance(item, dict) else {"full_name": str(item)})
            for item in data]
