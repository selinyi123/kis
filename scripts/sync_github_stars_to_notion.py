"""Incrementally sync GitHub Stars into the existing Notion database.

Zero runtime third-party dependencies. Designed for GitHub Actions, but can
also be run locally.

Persistent state lives in Notion itself via the ``标星时间`` date property.
The steady-state path is intentionally small:
1. read the latest ``标星时间`` watermark from Notion;
2. read GitHub stars newest-first until that watermark;
3. upsert only stars newer than the watermark, oldest-first.

Environment:
    NOTION_API_TOKEN       required for writes
    NOTION_DATA_SOURCE_ID  defaults to the user's existing GitHub Stars DB
    GITHUB_USERNAME        defaults to selinyi123
    GITHUB_TOKEN           optional; GitHub Actions supplies one automatically
"""

from __future__ import annotations

import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Iterable
from zoneinfo import ZoneInfo

GITHUB_API = "https://api.github.com"
NOTION_API = "https://api.notion.com/v1"
NOTION_VERSION = "2026-03-11"

DEFAULT_USER = "selinyi123"
DEFAULT_DATA_SOURCE_ID = "1c42c531-4691-4911-bccf-630a9366f744"
PER_PAGE = 100
MAX_BOOTSTRAP_PAGES = 20
REQUEST_TIMEOUT = 20

PROP_NAME = "名称"
PROP_STARS = "Star 数"
PROP_DESCRIPTION = "介绍"
PROP_PURPOSE = "功能作用"
PROP_OWNER = "归属"
PROP_FETCHED = "抓取日期"
PROP_URL = "链接"
PROP_STARRED_AT = "标星时间"


@dataclass(frozen=True)
class Star:
    starred_at: str
    full_name: str
    html_url: str
    description: str
    stars: int
    owner: str
    default_branch: str


def _request_json(
    url: str,
    *,
    method: str = "GET",
    headers: dict[str, str] | None = None,
    body: dict[str, Any] | None = None,
) -> tuple[Any, dict[str, str]]:
    req_headers = {"User-Agent": "kis-github-stars-notion-sync"}
    if headers:
        req_headers.update(headers)
    data = None
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        req_headers.setdefault("Content-Type", "application/json")
    req = urllib.request.Request(url, data=data, headers=req_headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as res:
            raw = res.read()
            payload = json.loads(raw.decode("utf-8")) if raw else None
            return payload, {k.lower(): v for k, v in res.headers.items()}
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"{method} {url} -> HTTP {exc.code}: {raw[:500]}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"{method} {url} -> network error: {exc.reason}") from exc


def github_headers(token: str | None = None) -> dict[str, str]:
    headers = {
        "Accept": "application/vnd.github.star+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def notion_headers(token: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {token}",
        "Notion-Version": NOTION_VERSION,
        "Content-Type": "application/json",
    }


def parse_star(item: dict[str, Any]) -> Star:
    repo = item.get("repo", item)
    owner = (repo.get("owner") or {}).get("login") or ""
    full_name = repo.get("full_name") or (
        f"{owner}/{repo.get('name', '')}" if owner and repo.get("name") else ""
    )
    return Star(
        starred_at=item.get("starred_at") or "",
        full_name=full_name,
        html_url=repo.get("html_url") or "",
        description=(repo.get("description") or "").strip(),
        stars=int(repo.get("stargazers_count") or 0),
        owner=owner,
        default_branch=repo.get("default_branch") or "main",
    )


def fetch_star_page(username: str, page: int, token: str | None) -> list[Star]:
    query = urllib.parse.urlencode(
        {
            "per_page": PER_PAGE,
            "page": page,
            "sort": "created",
            "direction": "desc",
        }
    )
    url = f"{GITHUB_API}/users/{urllib.parse.quote(username)}/starred?{query}"
    payload, _ = _request_json(url, headers=github_headers(token))
    if not isinstance(payload, list):
        raise RuntimeError("GitHub starred endpoint returned a non-list payload")
    stars = [parse_star(item) for item in payload]
    return [s for s in stars if s.starred_at and s.full_name and s.html_url]


def iter_new_stars(
    username: str,
    watermark: str | None,
    token: str | None,
    *,
    max_pages: int | None = None,
) -> Iterable[Star]:
    """Yield stars newest-first until an item is older than the watermark.

    Equality is intentionally included: GitHub timestamps have second-level
    precision, so two stars can share a timestamp. Duplicate detection in
    Notion makes replaying equality safe and prevents a same-second star from
    being skipped.
    """
    page = 1
    while max_pages is None or page <= max_pages:
        stars = fetch_star_page(username, page, token)
        if not stars:
            return
        for star in stars:
            if watermark and star.starred_at < watermark:
                return
            yield star
        if len(stars) < PER_PAGE:
            return
        page += 1


def query_notion(
    token: str,
    data_source_id: str,
    body: dict[str, Any],
) -> dict[str, Any]:
    payload, _ = _request_json(
        f"{NOTION_API}/data_sources/{data_source_id}/query",
        method="POST",
        headers=notion_headers(token),
        body=body,
    )
    if not isinstance(payload, dict):
        raise RuntimeError("Notion query returned an invalid payload")
    return payload


def latest_watermark(token: str, data_source_id: str) -> str | None:
    result = query_notion(
        token,
        data_source_id,
        {
            "page_size": 1,
            "filter": {
                "property": PROP_STARRED_AT,
                "date": {"is_not_empty": True},
            },
            "sorts": [{"property": PROP_STARRED_AT, "direction": "descending"}],
        },
    )
    rows = result.get("results") or []
    if not rows:
        return None
    prop = ((rows[0].get("properties") or {}).get(PROP_STARRED_AT) or {}).get("date")
    return (prop or {}).get("start")


def _plain_text(prop: dict[str, Any] | None, kind: str) -> str:
    if not prop:
        return ""
    chunks = prop.get(kind) or []
    return "".join(chunk.get("plain_text") or "" for chunk in chunks).strip()


def list_existing_rows(token: str, data_source_id: str) -> dict[str, str]:
    """One-time bootstrap helper: canonical GitHub URL -> Notion page id."""
    out: dict[str, str] = {}
    cursor: str | None = None
    while True:
        body: dict[str, Any] = {"page_size": 100}
        if cursor:
            body["start_cursor"] = cursor
        result = query_notion(token, data_source_id, body)
        for page in result.get("results") or []:
            props = page.get("properties") or {}
            url = ((props.get(PROP_URL) or {}).get("url") or "").strip()
            name = _plain_text(props.get(PROP_NAME), "title")
            if url:
                out[canonical_github_url(url)] = page["id"]
            elif name:
                out[f"name:{name.casefold()}"] = page["id"]
        if not result.get("has_more"):
            break
        cursor = result.get("next_cursor")
        if not cursor:
            break
    return out


def canonical_github_url(url: str) -> str:
    return url.rstrip("/").removesuffix(".git").casefold()


def find_existing_page(
    token: str,
    data_source_id: str,
    star: Star,
) -> str | None:
    by_url = query_notion(
        token,
        data_source_id,
        {
            "page_size": 2,
            "filter": {"property": PROP_URL, "url": {"equals": star.html_url}},
        },
    ).get("results") or []
    if by_url:
        return by_url[0]["id"]

    by_name = query_notion(
        token,
        data_source_id,
        {
            "page_size": 2,
            "filter": {"property": PROP_NAME, "title": {"equals": star.full_name}},
        },
    ).get("results") or []
    return by_name[0]["id"] if by_name else None


def patch_starred_at(token: str, page_id: str, starred_at: str) -> None:
    _request_json(
        f"{NOTION_API}/pages/{page_id}",
        method="PATCH",
        headers=notion_headers(token),
        body={
            "properties": {
                PROP_STARRED_AT: {"date": {"start": starred_at}},
            }
        },
    )


_BADGE_RE = re.compile(r"^\s*(?:\[?!?\[|<p\b|<div\b|<img\b|#|\!\[)", re.I)
_MARKDOWN_LINK_RE = re.compile(r"\[([^\]]+)\]\([^)]+\)")
_HTML_RE = re.compile(r"<[^>]+>")


def extract_readme_purpose(markdown: str) -> str:
    """Return a short deterministic README excerpt; no LLM/token use."""
    paragraphs: list[str] = []
    current: list[str] = []
    for raw in markdown.splitlines():
        line = raw.strip()
        if not line:
            if current:
                paragraphs.append(" ".join(current))
                current = []
            continue
        if _BADGE_RE.match(line):
            continue
        if line.startswith(("```", "---", "***")):
            continue
        current.append(line)
    if current:
        paragraphs.append(" ".join(current))

    for paragraph in paragraphs:
        text = _MARKDOWN_LINK_RE.sub(r"\1", paragraph)
        text = _HTML_RE.sub("", text)
        text = re.sub(r"[*_`~>#]", "", text)
        text = re.sub(r"\s+", " ", text).strip()
        if len(text) >= 24:
            return text[:280].rstrip()
    return ""


def fetch_readme(star: Star, token: str | None) -> str:
    path = f"/repos/{star.full_name}/readme"
    url = f"{GITHUB_API}{path}"
    headers = {
        "Accept": "application/vnd.github.raw+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "kis-github-stars-notion-sync", **headers},
    )
    try:
        with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as res:
            return res.read(256_000).decode("utf-8", errors="replace")
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            return ""
        raw = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"GET {url} -> HTTP {exc.code}: {raw[:300]}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"GET {url} -> network error: {exc.reason}") from exc


def build_purpose(star: Star, readme: str = "") -> str:
    source = star.description or extract_readme_purpose(readme)
    if not source:
        return ""
    source = source.strip().rstrip(".。")
    return f"该仓库主要用于：{source}。"


def notion_properties(star: Star, purpose: str, username: str) -> dict[str, Any]:
    today = datetime.now(ZoneInfo("Asia/Taipei")).date().isoformat()
    return {
        PROP_NAME: {
            "title": [
                {
                    "type": "text",
                    "text": {
                        "content": star.full_name[:2000],
                        "link": {"url": star.html_url},
                    },
                }
            ]
        },
        PROP_STARS: {"number": star.stars},
        PROP_DESCRIPTION: {
            "rich_text": (
                [{"type": "text", "text": {"content": star.description[:2000]}}]
                if star.description
                else []
            )
        },
        PROP_PURPOSE: {
            "rich_text": (
                [{"type": "text", "text": {"content": purpose[:2000]}}]
                if purpose
                else []
            )
        },
        PROP_OWNER: {
            "select": {"name": "本人" if star.owner.casefold() == username.casefold() else "外部"}
        },
        PROP_FETCHED: {"date": {"start": today}},
        PROP_URL: {"url": star.html_url},
        PROP_STARRED_AT: {"date": {"start": star.starred_at}},
    }


def create_notion_page(
    token: str,
    data_source_id: str,
    star: Star,
    purpose: str,
    username: str,
) -> None:
    _request_json(
        f"{NOTION_API}/pages",
        method="POST",
        headers=notion_headers(token),
        body={
            "parent": {"type": "data_source_id", "data_source_id": data_source_id},
            "properties": notion_properties(star, purpose, username),
        },
    )


def bootstrap(
    token: str,
    data_source_id: str,
    username: str,
    github_token: str | None,
) -> tuple[str | None, list[Star]]:
    """Find the newest already-synced star and use it as the initial boundary.

    This is the only path that reads the existing Notion rows. It prevents a
    first deployment from re-importing the user's entire historical star list.
    """
    existing = list_existing_rows(token, data_source_id)
    if not existing:
        stars = list(iter_new_stars(username, None, github_token, max_pages=1))
        if not stars:
            return None, []
        # No durable Notion watermark exists yet. Create only the newest star;
        # that row becomes the durable boundary for subsequent delta runs.
        return None, [stars[0]]

    newer: list[Star] = []
    for star in iter_new_stars(
        username, None, github_token, max_pages=MAX_BOOTSTRAP_PAGES
    ):
        key = canonical_github_url(star.html_url)
        name_key = f"name:{star.full_name.casefold()}"
        page_id = existing.get(key) or existing.get(name_key)
        if page_id:
            patch_starred_at(token, page_id, star.starred_at)
            return star.starred_at, newer
        newer.append(star)

    if newer:
        # No intersection found in the bounded bootstrap window. Refuse to
        # guess and bulk import history. Sync only the newest observed star;
        # its Notion ``标星时间`` becomes the durable boundary next run.
        return None, [newer[0]]
    return None, []


def sync() -> int:
    notion_token = os.getenv("NOTION_API_TOKEN", "").strip()
    if not notion_token:
        print("[kis] NOTION_API_TOKEN is not configured; sync skipped.")
        return 0

    data_source_id = os.getenv(
        "NOTION_DATA_SOURCE_ID", DEFAULT_DATA_SOURCE_ID
    ).strip()
    username = os.getenv("GITHUB_USERNAME", DEFAULT_USER).strip()
    github_token = os.getenv("GITHUB_TOKEN", "").strip() or None

    watermark = latest_watermark(notion_token, data_source_id)
    if watermark:
        candidates = list(iter_new_stars(username, watermark, github_token))
    else:
        watermark, candidates = bootstrap(
            notion_token, data_source_id, username, github_token
        )
        if watermark and not candidates:
            print(f"[kis] bootstrap complete at {watermark}; no historical backfill.")
            return 0

    # Oldest-first is deliberate. If a write fails midway, the Notion
    # watermark can only advance to the last successful older item; the failed
    # item and every newer item are retried next run.
    candidates = sorted(
        {star.html_url: star for star in candidates}.values(),
        key=lambda star: star.starred_at,
    )

    created = 0
    touched = 0
    for star in candidates:
        if watermark and star.starred_at < watermark:
            continue
        existing_page = find_existing_page(notion_token, data_source_id, star)
        if existing_page:
            patch_starred_at(notion_token, existing_page, star.starred_at)
            touched += 1
            continue

        readme = ""
        if not star.description:
            readme = fetch_readme(star, github_token)
        purpose = build_purpose(star, readme)
        create_notion_page(
            notion_token, data_source_id, star, purpose, username
        )
        created += 1

    print(
        f"[kis] GitHub Stars -> Notion complete: created={created}, "
        f"existing_watermark_updates={touched}"
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(sync())
    except Exception as exc:
        print(f"[kis] sync failed: {exc}", file=sys.stderr)
        raise
