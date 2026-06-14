"""Ingest a single web URL -> KnowledgeCard(web_clip) -> SQLite -> Obsidian.

KIS-008 baseline + KIS-009 optional extraction backend.

Extraction backends (--extractor):
    stdlib    only the stdlib baseline (default; zero deps, always works)
    crawl4ai  force Crawl4AI; fails explicitly if unavailable
    auto      try Crawl4AI, fall back to stdlib on failure (records fallback)

SSRF defense + blocked classification run BEFORE any extraction, so a blocked or
unsafe URL is never fetched and never reaches Crawl4AI.

Usage (PowerShell):
    python scripts/ingest_url.py https://example.com/article
    python scripts/ingest_url.py https://example.com --extractor auto
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Callable

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

from kis.card import now_iso  # noqa: E402
from kis.classify import classify_bookmark  # noqa: E402
from kis.connectors.web_url import UrlSafetyError, WebPageRaw, fetch_url, validate_url  # noqa: E402
from kis.extractors.base import ExtractedPage, OptionalDependencyMissing, extracted_to_card  # noqa: E402
from kis.extractors.crawl4ai_adapter import Crawl4AIExtractor, _run_crawl4ai  # noqa: E402
from kis.extractors.stdlib_html import StdlibExtractor  # noqa: E402
from kis.obsidian import export_card, render_webclip_md  # noqa: E402
from kis.store import Store  # noqa: E402
from kis.validate import load_schema, validate_card  # noqa: E402


@dataclass
class IngestResult:
    status: str          # refused | blocked | failed | invalid | inserted | updated | unchanged
    reason: str = ""
    card: dict[str, Any] | None = None


def _append_blocked(vault_out: str | None, record: dict[str, Any]) -> None:
    if not vault_out:
        return
    d = os.path.join(vault_out, "_blocked")
    os.makedirs(d, exist_ok=True)
    path = os.path.join(d, f"blocked-webclips-{datetime.now().strftime('%Y%m%d')}.jsonl")
    with open(path, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(record, ensure_ascii=False) + "\n")


def _run_extraction(url: str, mode: str, fetcher, crawl4ai_runner) -> ExtractedPage:
    """Resolve the extraction backend. May raise (forced crawl4ai failure)."""
    stdlib = StdlibExtractor(fetcher)
    if mode == "stdlib":
        return stdlib.extract(url)
    crawler = Crawl4AIExtractor(crawl4ai_runner or _run_crawl4ai)
    if mode == "crawl4ai":
        return crawler.extract(url)        # propagate failure -> forced mode errors out
    # auto: prefer crawl4ai, fall back to stdlib
    try:
        return crawler.extract(url)
    except Exception as e:
        page = stdlib.extract(url)
        page.extraction_engine = "stdlib"
        page.extraction_status = "fallback"
        page.extraction_error = f"crawl4ai_failed: {e}"
        return page


def ingest_url(
    url: str,
    db_path: str,
    vault_path: str | None,
    mode: str = "stdlib",
    fetcher: Callable[[str], WebPageRaw] = fetch_url,
    crawl4ai_runner: Callable[[str], dict] | None = None,
    batch_id: str | None = None,
) -> IngestResult:
    """Reusable pipeline. fetcher + crawl4ai_runner are injectable for offline tests."""
    batch_id = batch_id or "wc_" + datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")

    # 1) SSRF / scheme defense — refuse before any fetch or extractor (incl. crawl4ai).
    try:
        validate_url(url)
    except UrlSafetyError as e:
        return IngestResult(status="refused", reason=str(e))

    # 2) Pre-classify by URL — blocked targets are never fetched/extracted/stored.
    if classify_bookmark("", url, "")["decision"] == "blocked":
        _append_blocked(vault_path, {"ts": now_iso(), "url": url, "stage": "pre-fetch",
                                     "reason": "blocked", "import_batch_id": batch_id})
        return IngestResult(status="blocked", reason="url classified blocked")

    # 3) Extraction (stdlib baseline / optional crawl4ai)
    try:
        page = _run_extraction(url, mode, fetcher, crawl4ai_runner)
    except OptionalDependencyMissing as e:
        return IngestResult(status="failed", reason=f"crawl4ai unavailable: {e}")
    except Exception as e:
        return IngestResult(status="failed", reason=f"extraction failed: {e}")

    if page.extraction_status == "failed":
        return IngestResult(status="failed", reason=page.extraction_error or "extraction failed")

    # 4) Re-classify with the real title; block if content reveals a blocked target.
    cls = classify_bookmark(page.title, page.url, page.site_name)
    if cls["decision"] == "blocked":
        _append_blocked(vault_path, {"ts": now_iso(), "url": url, "stage": "post-fetch",
                                     "title": page.title, "reason": "blocked", "import_batch_id": batch_id})
        return IngestResult(status="blocked", reason="content classified blocked")

    card = extracted_to_card(page, cls, import_batch_id=batch_id)
    errors = validate_card(card, load_schema())
    if errors:
        return IngestResult(status="invalid", reason=errors[0], card=card)

    os.makedirs(os.path.dirname(os.path.abspath(db_path)), exist_ok=True)
    store = Store(db_path)
    status = store.upsert(card)
    store.close()
    if vault_path and status != "unchanged":
        export_card(card, vault_path, rel_dir=f"Web-Clips/{cls['folder']}", renderer=render_webclip_md)
    return IngestResult(status=status, card=card)


def main() -> int:
    ap = argparse.ArgumentParser(description="Ingest a single web URL into KIS.")
    ap.add_argument("url")
    ap.add_argument("--db", default="data/kis.db")
    ap.add_argument("--obsidian-out", default="vault_out")
    ap.add_argument("--extractor", choices=["stdlib", "crawl4ai", "auto"], default="stdlib")
    ap.add_argument("--no-obsidian", action="store_true")
    ap.add_argument("--timeout", type=int, default=10)
    args = ap.parse_args()

    out = None if args.no_obsidian else args.obsidian_out
    res = ingest_url(args.url, args.db, out, mode=args.extractor,
                     fetcher=lambda u: fetch_url(u, timeout=args.timeout))
    print(f"[kis] web clip ({args.extractor}): {res.status}" + (f"  ({res.reason})" if res.reason else ""))
    if res.card:
        c = res.card
        print(f"      title: {c['content']['title']}")
        print(f"      engine: {c['source'].get('extraction_engine')}  status: {c['source'].get('extraction_status')}")
        print(f"      category: {c['enrichment']['category']}  sensitivity: {c['safety']['sensitivity']}  id: {c['id']}")
    if out:
        print(f"      web_clip_cards_in_db: {Store(args.db).count('web_clip')}")
    return 0 if res.status in {"inserted", "updated", "unchanged"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
