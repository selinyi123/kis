"""KnowledgeCard construction + deterministic identity + URL normalization.

Identity rules (idempotency core, reused from DPMS discovery + ClipVault outbox):
  * ``stable_id(source_type, normalized_url)`` -> primary upsert key, stable
    across re-runs; same URL bookmarked twice dedups to one card.
  * ``content_hash(*parts)`` -> changes only when source content changes,
    enabling update / stale detection later.

Pure module: no DB, no network. Source-imported cards are provenance, so they
carry authority="source" and evidence_level="source".
"""

from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from typing import Any
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from . import SCHEMA_VERSION

# Tracking / campaign params stripped during URL normalization so the same link
# with different ad params dedups to one card.
_TRACKING_PARAMS = {
    "utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content", "utm_id",
    "gclid", "gad_source", "gad_campaignid", "gbraid", "wbraid", "fbclid", "msclkid",
    "c_id", "c_agid", "c_crid", "c_kwid", "c_ims", "c_pms", "c_nw", "c_dvc",
    "ref", "ref_src", "spm", "from", "src", "share_source", "_hsenc", "_hsmi",
}


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def add_date_to_iso(add_date: str | int | None) -> str:
    """Convert a Netscape bookmark ADD_DATE (unix seconds) to ISO-8601 UTC."""
    if add_date in (None, ""):
        return now_iso()
    try:
        ts = int(add_date)
    except (TypeError, ValueError):
        return now_iso()
    return datetime.fromtimestamp(ts, tz=timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def normalize_url(url: str) -> str:
    """Canonicalize a URL: lowercase scheme/host, drop default port and fragment,
    strip tracking params, drop a bare trailing slash on the path."""
    url = (url or "").strip()
    if not url:
        return url
    parts = urlsplit(url)
    scheme = parts.scheme.lower() or "https"
    host = parts.hostname or ""
    host = host.lower()
    netloc = host
    if parts.port and not ((scheme == "http" and parts.port == 80) or (scheme == "https" and parts.port == 443)):
        netloc = f"{host}:{parts.port}"
    query_pairs = [(k, v) for k, v in parse_qsl(parts.query, keep_blank_values=False)
                   if k.lower() not in _TRACKING_PARAMS]
    query = urlencode(query_pairs)
    path = parts.path
    if path == "/":
        path = ""
    return urlunsplit((scheme, netloc, path, query, ""))


def url_hash(normalized_url: str) -> str:
    return hashlib.sha256(normalized_url.encode("utf-8")).hexdigest()[:16]


def stable_id(source_type: str, normalized_url: str) -> str:
    digest = hashlib.sha256(f"{source_type}|{normalized_url}".encode("utf-8")).hexdigest()
    return f"kc_{digest[:16]}"


def content_hash(*parts: str) -> str:
    return hashlib.sha256("\n".join(p or "" for p in parts).encode("utf-8")).hexdigest()


def new_card(
    *,
    source_type: str,
    url: str,
    title: str,
    body_md: str,
    content_hash_value: str,
    lang: str = "unknown",
    captured_at: str | None = None,
    created_at: str | None = None,
    raw_ref: str | None = None,
    folder_path: str | None = None,
    raw_title: str | None = None,
    import_batch_id: str | None = None,
    summary: str = "",
    tags: list[str] | None = None,
    category: str = "",
    topics: list[str] | None = None,
    evidence_level: str = "source",
    authority: str = "source",
    sensitivity: str = "public",
    projects: list[str] | None = None,
    wikilinks: list[str] | None = None,
) -> dict[str, Any]:
    """Assemble a schema-valid KnowledgeCard (v0.2.0) with safe defaults.

    LLM enrichment (summary/value scoring) is v0.3; until then value_score=0 /
    value_level=cold and evidence_level reflects the raw source.
    """
    captured = captured_at or now_iso()
    created = created_at or captured
    norm = normalize_url(url)
    card: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "id": stable_id(source_type, norm),
        "content_hash": content_hash_value,
        "source": {
            "source_type": source_type,
            "url": url,
            "source_id": url_hash(norm),
            "captured_at": captured,
            "normalized_url": norm,
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
            "evidence_level": evidence_level,
            "authority": authority,
        },
        "linkage": {
            "projects": projects or [],
            "related_cards": [],
            "wikilinks": wikilinks or [],
        },
        "lifecycle": {
            "state": "inbox",
            "created_at": created,
            "updated_at": captured,
            "version": 1,
        },
        "safety": {
            "secret_redacted": False,
            "injection_scanned": False,
            "sensitivity": sensitivity,
        },
    }
    src = card["source"]
    if raw_ref is not None:
        src["raw_ref"] = raw_ref
    if folder_path:
        src["folder_path"] = folder_path
    if raw_title is not None:
        src["raw_title"] = raw_title
    if import_batch_id is not None:
        src["import_batch_id"] = import_batch_id
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
    haystack = (text or "").lower()
    return [proj for proj, kws in _PROJECT_KEYWORDS.items() if any(k.lower() in haystack for k in kws)]


def github_star_card(repo: dict[str, Any]) -> dict[str, Any]:
    """Map a GitHub starred-repo API object into a KnowledgeCard (source_type=github_star)."""
    full_name = repo.get("full_name") or repo.get("name") or "unknown/unknown"
    url = repo.get("html_url") or f"https://github.com/{full_name}"
    description = (repo.get("description") or "").strip()
    language = repo.get("language") or ""
    stars = repo.get("stargazers_count")
    topics = list(repo.get("topics") or [])

    tags = ([f"lang:{language}"] if language else []) + topics

    body_lines = [description] if description else []
    meta = []
    if language:
        meta.append(f"language: {language}")
    if stars is not None:
        meta.append(f"stars: {stars}")
    if repo.get("pushed_at"):
        meta.append(f"pushed_at: {repo['pushed_at']}")
    if meta:
        body_lines += ["", " | ".join(meta)]
    body_md = "\n".join(body_lines).strip() or full_name

    link_text = f"{full_name} {description} {language} {' '.join(topics)}"
    return new_card(
        source_type="github_star",
        url=url,
        title=full_name,
        body_md=body_md,
        content_hash_value=content_hash(full_name, description, language),
        lang="en",
        raw_ref=full_name,
        summary=description,
        tags=tags,
        category="repo",
        topics=topics,
        projects=infer_projects(link_text),
    )
