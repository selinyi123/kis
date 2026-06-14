"""Netscape bookmark HTML connector (KIS-007).

parse_bookmarks_html(path) -> list[BookmarkItem]
bookmark_to_card(item)     -> KnowledgeCard

Pure stdlib (html.parser). Tracks folder nesting via <H3>/<DL> so each link
keeps its folder_path.
"""

from __future__ import annotations

from dataclasses import dataclass
from html.parser import HTMLParser
from typing import Any

from ..card import add_date_to_iso, content_hash, infer_projects, new_card, normalize_url
from ..classify import classify_bookmark


@dataclass
class BookmarkItem:
    title: str
    url: str
    folder_path: str
    add_date: str | None


class _BookmarkParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.items: list[BookmarkItem] = []
        self._folder_stack: list[str | None] = []
        self._pending_folder: str | None = None
        self._cap_h3 = False
        self._h3_text: list[str] = []
        self._cap_a = False
        self._a_text: list[str] = []
        self._a_href: str | None = None
        self._a_add_date: str | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.lower()
        if tag == "h3":
            self._cap_h3 = True
            self._h3_text = []
        elif tag == "dl":
            # A <DL> opens the children of the most recent <H3> (or root).
            self._folder_stack.append(self._pending_folder)
            self._pending_folder = None
        elif tag == "a":
            d = dict(attrs)
            self._cap_a = True
            self._a_text = []
            self._a_href = d.get("href")
            self._a_add_date = d.get("add_date")

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if tag == "h3":
            self._cap_h3 = False
            self._pending_folder = "".join(self._h3_text).strip()
        elif tag == "dl":
            if self._folder_stack:
                self._folder_stack.pop()
        elif tag == "a":
            if self._cap_a and self._a_href:
                folder = "/".join(f for f in self._folder_stack if f)
                self.items.append(BookmarkItem(
                    title="".join(self._a_text).strip() or self._a_href,
                    url=self._a_href.strip(),
                    folder_path=folder,
                    add_date=self._a_add_date,
                ))
            self._cap_a = False
            self._a_href = None
            self._a_add_date = None

    def handle_data(self, data: str) -> None:
        if self._cap_h3:
            self._h3_text.append(data)
        elif self._cap_a:
            self._a_text.append(data)


def parse_bookmarks_html(path: str) -> list[BookmarkItem]:
    with open(path, "r", encoding="utf-8", errors="replace") as fh:
        html = fh.read()
    parser = _BookmarkParser()
    parser.feed(html)
    return parser.items


def bookmark_to_card(item: BookmarkItem, import_batch_id: str | None = None) -> dict[str, Any]:
    """Build a KnowledgeCard from a bookmark. Classification (category /
    sensitivity) is computed deterministically here. Caller decides whether to
    store based on the classification's ``decision`` (blocked items are skipped).
    """
    cls = classify_bookmark(item.title, item.url, item.folder_path)
    captured = None  # default: now
    created = add_date_to_iso(item.add_date)
    norm = normalize_url(item.url)
    body = (
        f"## Source\n"
        f"- URL: {item.url}\n"
        f"- Folder: {item.folder_path or '(root)'}\n"
        f"- Imported at: {created}\n\n"
        f"## Initial Classification\n- category: {cls['category']}\n- sensitivity: {cls['sensitivity']}\n\n"
        f"## Notes\n\n## Next Action\n- [ ] review"
    )
    return new_card(
        source_type="web_bookmark",
        url=item.url,
        title=item.title,
        body_md=body,
        content_hash_value=content_hash(item.title, norm, item.folder_path),
        lang="unknown",
        captured_at=captured,
        created_at=created,
        folder_path=item.folder_path,
        raw_title=item.title,
        import_batch_id=import_batch_id,
        category=cls["category"],
        sensitivity=cls["sensitivity"],
        projects=infer_projects(f"{item.title} {norm} {item.folder_path}"),
    )
