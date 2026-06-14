"""Render a KnowledgeCard to an Obsidian note (frontmatter + wikilinks).

Mirrors the ClipVault Obsidian convention: YAML frontmatter for metadata,
[[wikilinks]] to related projects/cards so the vault graph connects. Pure string
rendering + file write; no vault assumptions beyond an output directory.
"""

from __future__ import annotations

import os
import re
from typing import Any

_SLUG_RE = re.compile(r"[^0-9A-Za-z一-鿿_-]+")


def _slug(text: str) -> str:
    s = _SLUG_RE.sub("-", text).strip("-")
    return s[:80] or "card"


def _yaml_list(items: list[str]) -> str:
    if not items:
        return "[]"
    return "[" + ", ".join(json_safe(i) for i in items) + "]"


def json_safe(value: str) -> str:
    return '"' + value.replace('"', '\\"') + '"'


def render_card_md(card: dict[str, Any]) -> str:
    src = card["source"]
    enr = card["enrichment"]
    life = card["lifecycle"]
    link = card["linkage"]

    fm = [
        "---",
        f"kis_id: {card['id']}",
        f"connector: {src['connector']}",
        f"url: {json_safe(src['url'])}",
        f"captured_at: {src['captured_at']}",
        f"category: {enr.get('category', '')}",
        f"value_level: {enr.get('value_level', 'cold')}",
        f"evidence_level: {enr.get('evidence_level', 'heuristic')}",
        f"state: {life.get('state', 'inbox')}",
        f"tags: {_yaml_list(enr.get('tags', []))}",
        f"projects: {_yaml_list(link.get('projects', []))}",
        "---",
        "",
    ]

    body = [f"# {card['content']['title']}", ""]
    if enr.get("summary"):
        body += [f"> {enr['summary']}", ""]
    body += [card["content"]["body_md"], ""]
    body += [f"**来源**: [{src['url']}]({src['url']})", ""]

    proj_links = [f"[[{p}]]" for p in link.get("projects", [])]
    if proj_links:
        body += ["**关联项目**: " + " ".join(proj_links), ""]
    wls = link.get("wikilinks", [])
    if wls:
        body += ["**相关**: " + " ".join(wls), ""]

    return "\n".join(fm + body)


def export_card(card: dict[str, Any], out_dir: str) -> str:
    """Write one card to <out_dir>/<connector>/<title-slug>.md. Returns the path."""
    sub = os.path.join(out_dir, card["source"]["connector"])
    os.makedirs(sub, exist_ok=True)
    name = _slug(card["content"]["title"]) + ".md"
    path = os.path.join(sub, name)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(render_card_md(card))
    return path
