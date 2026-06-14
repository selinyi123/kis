"""Render a KnowledgeCard to an Obsidian note (frontmatter + wikilinks).

Mirrors the ClipVault Obsidian convention: YAML frontmatter for metadata,
[[wikilinks]] to related projects so the vault graph connects. Pure string
rendering + file write; the caller chooses the relative directory.
"""

from __future__ import annotations

import os
import re
from typing import Any, Callable

_SLUG_RE = re.compile(r"[^0-9A-Za-z一-鿿_-]+")


def _slug(text: str) -> str:
    s = _SLUG_RE.sub("-", text or "").strip("-")
    return s[:80] or "card"


def _q(value: str) -> str:
    return '"' + (value or "").replace('"', '\\"') + '"'


def _yaml_list(items: list[str]) -> str:
    return "[" + ", ".join(_q(i) for i in items) + "]" if items else "[]"


def _frontmatter(card: dict[str, Any]) -> list[str]:
    src, enr, life, saf = card["source"], card["enrichment"], card["lifecycle"], card["safety"]
    projects = card["linkage"].get("projects", [])
    return [
        "---",
        f"card_id: {card['id']}",
        f"source_type: {src['source_type']}",
        f"source_url: {_q(src['url'])}",
        f"source_id: {src['source_id']}",
        f"project: {projects[0] if projects else 'general'}",
        f"category: {enr.get('category', '')}",
        f"folder_path: {_q(src.get('folder_path', ''))}",
        f"captured_at: {src['captured_at']}",
        f"content_hash: {card['content_hash']}",
        f"sensitivity: {saf.get('sensitivity', 'public')}",
        f"authority: {enr.get('authority', 'source')}",
        f"status: {life.get('state', 'inbox')}",
        f"evidence_level: {enr.get('evidence_level', 'source')}",
        f"value_level: {enr.get('value_level', 'cold')}",
        f"tags: {_yaml_list(enr.get('tags', []))}",
        f"projects: {_yaml_list(projects)}",
        "---",
        "",
    ]


def render_card_md(card: dict[str, Any]) -> str:
    """Generic renderer (used by GitHub Stars and any rich-body card)."""
    enr, link, src = card["enrichment"], card["linkage"], card["source"]
    out = _frontmatter(card)
    out += [f"# {card['content']['title']}", ""]
    if enr.get("summary"):
        out += [f"> {enr['summary']}", ""]
    out += [card["content"]["body_md"], "", f"**来源**: [{src['url']}]({src['url']})", ""]
    proj_links = [f"[[{p}]]" for p in link.get("projects", [])]
    if proj_links:
        out += ["**关联项目**: " + " ".join(proj_links), ""]
    return "\n".join(out)


def render_bookmark_md(card: dict[str, Any]) -> str:
    """Bookmark template (KIS-007 spec). Body already holds the Source/Notes
    sections; frontmatter carries provenance."""
    link = card["linkage"]
    out = _frontmatter(card)
    out += [f"# {card['content']['title']}", "", card["content"]["body_md"], ""]
    proj_links = [f"[[{p}]]" for p in link.get("projects", [])]
    if proj_links:
        out += ["", "**关联项目**: " + " ".join(proj_links), ""]
    return "\n".join(out)


def export_card(
    card: dict[str, Any],
    out_dir: str,
    rel_dir: str | None = None,
    renderer: Callable[[dict[str, Any]], str] = render_card_md,
) -> str:
    """Write one card to <out_dir>/<rel_dir>/<title-slug>.md. Returns the path."""
    rel = rel_dir if rel_dir is not None else card["source"]["source_type"]
    sub = os.path.join(out_dir, *rel.split("/")) if rel else out_dir
    os.makedirs(sub, exist_ok=True)
    path = os.path.join(sub, _slug(card["content"]["title"]) + ".md")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(renderer(card))
    return path
