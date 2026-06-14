"""KnowledgeCard construction + deterministic identity.

Identity rules (idempotency core, reused from DPMS discovery + ClipVault outbox):
  * ``stable_id(connector, url)``  -> primary upsert key, same across re-runs.
  * ``content_hash(title, body)``  -> changes only when source content changes,
    enabling update / stale detection later (v0.2).

This module is pure: no DB, no network. Easy to unit-test (DPMS scoring style).
"""

from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from typing import Any

from . import SCHEMA_VERSION


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def stable_id(connector: str, url: str) -> str:
    digest = hashlib.sha256(f"{connector}|{url}".encode("utf-8")).hexdigest()
    return f"kc_{digest[:16]}"


def content_hash(title: str, body: str) -> str:
    return hashlib.sha256(f"{title}\n{body}".encode("utf-8")).hexdigest()


def new_card(
    *,
    connector: str,
    url: str,
    title: str,
    body_md: str,
    lang: str = "unknown",
    captured_at: str | None = None,
    raw_ref: str | None = None,
    summary: str = "",
    tags: list[str] | None = None,
    category: str = "",
    topics: list[str] | None = None,
    projects: list[str] | None = None,
    wikilinks: list[str] | None = None,
) -> dict[str, Any]:
    """Assemble a schema-valid KnowledgeCard dict with safe v0.1 defaults.

    Enrichment defaults to a deterministic heuristic placeholder; real LLM
    summary/tags/score arrive in v0.2 but the schema fields exist now so the
    contract never has to break.
    """
    ts = captured_at or now_iso()
    card: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "id": stable_id(connector, url),
        "content_hash": content_hash(title, body_md),
        "source": {
            "connector": connector,
            "url": url,
            "captured_at": ts,
        },
        "content": {
            "title": title,
            "body_md": body_md,
            "lang": lang,
            "media": [],
        },
        "enrichment": {
            "summary": summary,
            "tags": tags or [],
            "category": category,
            "topics": topics or [],
            "value_score": 0,
            "value_level": "cold",
            "evidence_level": "heuristic",
        },
        "linkage": {
            "projects": projects or [],
            "related_cards": [],
            "wikilinks": wikilinks or [],
        },
        "lifecycle": {
            "state": "inbox",
            "created_at": ts,
            "updated_at": ts,
            "version": 1,
        },
        "safety": {
            # v0.1: GitHub Stars are public metadata; secret/injection scanning
            # is wired in v0.2 (KIS-016). Honest defaults until then.
            "secret_redacted": False,
            "injection_scanned": False,
        },
    }
    if raw_ref is not None:
        card["source"]["raw_ref"] = raw_ref
    return card


# --- Active-project linkage (deterministic v0.1 rule, DPMS strategy style) -----

_PROJECT_KEYWORDS: dict[str, tuple[str, ...]] = {
    "DPMS-Platform": ("lottery", "抽奖", "playwright", "anti-bot", "captcha", "automation"),
    "ClipVault": ("clipboard", "剪切板", "obsidian", "ime", "android", "sync"),
    "prompt-performance-engine": ("prompt", "llm", "evaluation", "评测", "agent skill", "skills"),
    "KIS": ("knowledge", "memory", "crawler", "rag", "knowledge graph", "知识", "记忆", "爬虫", "搜索", "search"),
}


def infer_projects(text: str) -> list[str]:
    """Map a card's text to active projects by keyword (rule-based, no LLM)."""
    haystack = text.lower()
    hits = [proj for proj, kws in _PROJECT_KEYWORDS.items() if any(k.lower() in haystack for k in kws)]
    return hits


def github_star_card(repo: dict[str, Any]) -> dict[str, Any]:
    """Map a GitHub starred-repo API object into a KnowledgeCard.

    Expected keys from `gh api users/<u>/starred`: full_name, html_url,
    description, language, stargazers_count, topics (optional), pushed_at.
    """
    full_name = repo.get("full_name") or repo.get("name") or "unknown/unknown"
    url = repo.get("html_url") or f"https://github.com/{full_name}"
    description = (repo.get("description") or "").strip()
    language = repo.get("language") or ""
    stars = repo.get("stargazers_count")
    topics = list(repo.get("topics") or [])

    tags = []
    if language:
        tags.append(f"lang:{language}")
    tags.extend(topics)

    body_lines = [description] if description else []
    meta = []
    if language:
        meta.append(f"language: {language}")
    if stars is not None:
        meta.append(f"stars: {stars}")
    if repo.get("pushed_at"):
        meta.append(f"pushed_at: {repo['pushed_at']}")
    if meta:
        body_lines.append("")
        body_lines.append(" | ".join(meta))
    body_md = "\n".join(body_lines).strip()

    link_text = f"{full_name} {description} {language} {' '.join(topics)}"

    return new_card(
        connector="github_stars",
        url=url,
        title=full_name,
        body_md=body_md or full_name,
        lang="en",
        raw_ref=full_name,
        summary=description,
        tags=tags,
        category="repo",
        topics=topics,
        projects=infer_projects(link_text),
        wikilinks=[],
    )
