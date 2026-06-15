"""Turn a raw source item into a KnowledgeCard (KIS-018).

Reuses the existing card builders so external inbox cards share ONE schema with
the rest of KIS. Everything lands in lifecycle.state=inbox (new_card default).
"""

from __future__ import annotations

from typing import Any

from ..card import content_hash, github_star_card, infer_projects, new_card, normalize_url
from ..classify import classify_bookmark
from ..connectors.bookmarks import BookmarkItem, bookmark_to_card


def _apply_overrides(card: dict[str, Any], source_project: str | None, category: str | None) -> dict[str, Any]:
    if source_project:
        card["linkage"]["projects"] = [source_project]
    if category:
        card["enrichment"]["category"] = category
    return card


def build_card(source_type: str, raw: dict[str, Any], source_project: str | None = None,
               category: str | None = None) -> dict[str, Any]:
    if source_type == "github_star":
        card = github_star_card(raw)
    elif source_type == "web_bookmark":
        item = BookmarkItem(title=raw.get("title", ""), url=raw.get("url", ""),
                            folder_path=raw.get("folder", raw.get("folder_path", "")),
                            add_date=raw.get("add_date"))
        card = bookmark_to_card(item)
    elif source_type == "web_clip":
        card = _web_clip_card(raw)
    else:
        raise ValueError(f"unknown source_type: {source_type}")
    return _apply_overrides(card, source_project, category)


def _web_clip_card(raw: dict[str, Any]) -> dict[str, Any]:
    url = (raw.get("url") or "").strip()
    if not url:
        raise ValueError("web_clip item missing url")
    title = (raw.get("title") or url).strip()
    text = (raw.get("text") or "").strip()
    norm = normalize_url(url)
    source = raw.get("source") or "manual"
    body = f"## Source\n- URL: {url}\n- Provided by: {source}\n\n## Content\n{text or '(empty)'}"
    return new_card(
        source_type="web_clip", url=url, title=title, body_md=body,
        content_hash_value=content_hash(norm, title, text),
        lang="unknown", captured_at=raw.get("captured_at"),
        category="web_clip", text_preview=text[:4000],
        projects=infer_projects(f"{title} {norm} {text[:500]}"),
    )
