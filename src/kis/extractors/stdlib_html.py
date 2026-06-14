"""Stdlib extraction backend (KIS-009) — wraps the KIS-008 baseline.

Always available, zero third-party deps. This is the backend that must keep
working even when crawl4ai is not installed.
"""

from __future__ import annotations

from typing import Callable

from ..connectors.web_url import WebPageRaw, extract_web_page, fetch_url
from .base import ExtractedPage, Extractor


class StdlibExtractor(Extractor):
    name = "stdlib"

    def __init__(self, fetcher: Callable[[str], WebPageRaw] = fetch_url):
        self.fetcher = fetcher

    def extract(self, url: str) -> ExtractedPage:
        raw = self.fetcher(url)
        page = extract_web_page(raw)
        failed = bool(page.fetch_error)
        return ExtractedPage(
            url=page.url,
            normalized_url=page.normalized_url,
            title=page.title,
            description=page.description or None,
            text_preview=page.text_preview,
            clean_markdown=None,           # stdlib baseline does not produce markdown
            structured_data={},
            extraction_engine="stdlib",
            extraction_status="failed" if failed else "success",
            extraction_error=page.fetch_error,
            site_name=page.site_name,
            lang=page.lang,
            http_status=page.http_status,
            fetched_at=page.fetched_at,
            fetch_error=page.fetch_error,
        )
