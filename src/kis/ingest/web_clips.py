"""Parse a manual web-clip JSONL export into clip dicts (KIS-018). No network.

Each line: {"url","title","text","source","captured_at"}. Malformed lines are
reported as errors by the runner, not silently dropped.
"""

from __future__ import annotations

import json
from typing import Any


def parse(path: str) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    with open(path, encoding="utf-8") as fh:
        for n, line in enumerate(fh, 1):
            line = line.strip()
            if not line:
                continue
            try:
                items.append(json.loads(line))
            except json.JSONDecodeError as e:
                items.append({"_parse_error": f"line {n}: {e}", "_raw": line[:200]})
    return items
