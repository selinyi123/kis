"""Parse a browser bookmark HTML export into bookmark dicts (KIS-018).

Reuses the KIS-007 Netscape parser (Chrome/Edge/Firefox export format).
"""

from __future__ import annotations

from typing import Any

from ..connectors.bookmarks import parse_bookmarks_html


def parse(path: str) -> list[dict[str, Any]]:
    items = parse_bookmarks_html(path)
    return [{"title": i.title, "url": i.url, "folder": i.folder_path, "add_date": i.add_date}
            for i in items]
