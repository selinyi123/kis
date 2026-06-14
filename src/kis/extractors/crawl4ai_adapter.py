"""Optional Crawl4AI extraction backend (KIS-009).

HARD RULES:
  * crawl4ai is imported lazily inside the runner — never at module top level,
    so importing this module never requires crawl4ai and never breaks KIS-008.
  * This adapter NEVER validates URLs or decides blocked/allowed — the caller
    (ingest_url, KIS-008) must run validate_url + classify + blocked + normalize
    BEFORE invoking the adapter.
  * The actual crawl4ai call lives behind an injectable ``runner`` so unit tests
    mock it (no real network, no browser launch).

Runner contract: ``runner(url) -> dict`` with keys:
    title, description, markdown, text, structured, http_status, site_name,
    lang, error.  May raise OptionalDependencyMissing if crawl4ai is absent.
"""

from __future__ import annotations

from typing import Any, Callable

from ..card import normalize_url, now_iso
from .base import ExtractedPage, Extractor, MAX_MARKDOWN, MAX_PREVIEW, OptionalDependencyMissing


def _run_crawl4ai(url: str, timeout: int = 30) -> dict[str, Any]:
    """Real backend (smoke/manual only — never exercised by unit tests).

    Lazily imports crawl4ai and runs a single-page extraction. Any import
    failure becomes a controlled OptionalDependencyMissing.
    """
    try:
        from crawl4ai import AsyncWebCrawler  # type: ignore
    except ImportError as e:  # controlled, not a raw ImportError leak
        raise OptionalDependencyMissing(
            "crawl4ai is not installed. Install it (`pip install crawl4ai`) or use --extractor stdlib."
        ) from e

    import asyncio

    async def _go() -> Any:
        async with AsyncWebCrawler() as crawler:
            return await crawler.arun(url=url)

    res = asyncio.run(_go())
    md = getattr(res, "markdown", None)
    if md is not None and not isinstance(md, str):
        md = getattr(md, "raw_markdown", None) or str(md)
    meta = getattr(res, "metadata", {}) or {}
    return {
        "title": meta.get("title"),
        "description": meta.get("description"),
        "markdown": md,
        "text": (md or "")[:MAX_PREVIEW],
        "structured": {},
        "http_status": getattr(res, "status_code", 0) or 0,
        "site_name": meta.get("og:site_name") or "",
        "lang": meta.get("language") or "unknown",
        "error": None if getattr(res, "success", True) else getattr(res, "error_message", "crawl4ai failed"),
    }


class Crawl4AIExtractor(Extractor):
    name = "crawl4ai"

    def __init__(self, runner: Callable[[str], dict[str, Any]] = _run_crawl4ai):
        self.runner = runner

    def extract(self, url: str) -> ExtractedPage:
        res = self.runner(url)  # may raise OptionalDependencyMissing
        if res.get("error"):
            raise RuntimeError(f"crawl4ai extraction error: {res['error']}")
        md = (res.get("markdown") or "")
        md = md[:MAX_MARKDOWN] if md else None
        text = (res.get("text") or (md or ""))[:MAX_PREVIEW]
        return ExtractedPage(
            url=url,
            normalized_url=normalize_url(url),
            title=res.get("title") or url,
            description=res.get("description"),
            text_preview=text,
            clean_markdown=md,
            structured_data=res.get("structured") or {},
            extraction_engine="crawl4ai",
            extraction_status="success",
            extraction_error=None,
            site_name=res.get("site_name") or "",
            lang=res.get("lang") or "unknown",
            http_status=int(res.get("http_status") or 0),
            fetched_at=now_iso(),
            fetch_error=None,
        )
