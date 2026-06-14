"""Extraction interface + unified result + web_clip card builder (KIS-009)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ..card import content_hash, infer_projects, new_card

MAX_MARKDOWN = 20_000
MAX_PREVIEW = 4_000


class OptionalDependencyMissing(RuntimeError):
    """Raised when an optional extraction backend (e.g. crawl4ai) is unavailable."""


@dataclass
class ExtractedPage:
    url: str
    normalized_url: str
    title: str
    description: str | None
    text_preview: str
    clean_markdown: str | None
    structured_data: dict[str, Any]
    extraction_engine: str          # "stdlib" | "crawl4ai"
    extraction_status: str          # "success" | "fallback" | "failed"
    extraction_error: str | None
    site_name: str = ""
    lang: str = "unknown"
    http_status: int = 0
    fetched_at: str = ""
    fetch_error: str | None = None


class Extractor:
    """Backend that turns an (already validated/normalized) URL into ExtractedPage."""
    name: str = "base"

    def extract(self, url: str) -> ExtractedPage:  # pragma: no cover - interface
        raise NotImplementedError


def extracted_to_card(page: ExtractedPage, cls: dict[str, str], import_batch_id: str | None = None) -> dict[str, Any]:
    """Build a web_clip KnowledgeCard from an ExtractedPage + classification."""
    md = page.clean_markdown[:MAX_MARKDOWN] if page.clean_markdown else None
    preview = (page.text_preview or "")[:MAX_PREVIEW]
    body = (
        f"## Source\n- URL: {page.url}\n- Site: {page.site_name}\n"
        f"- Fetched at: {page.fetched_at}\n- HTTP status: {page.http_status}\n\n"
        f"## Extraction\n- Engine: {page.extraction_engine}\n"
        f"- Status: {page.extraction_status}\n- Error: {page.extraction_error or '(none)'}\n\n"
        f"## Description\n{page.description or '(none)'}\n\n"
        + (f"## Clean Markdown\n{md}\n\n" if md else "")
        + f"## Text Preview\n{preview or '(empty)'}\n\n"
        f"## Initial Classification\n- Category: {cls['category']}\n- Sensitivity: {cls['sensitivity']}\n\n"
        f"## Next Action\n- [ ] review\n- [ ] summarize\n- [ ] decide whether to promote to canonical"
    )
    return new_card(
        source_type="web_clip",
        url=page.url,
        title=page.title,
        body_md=body,
        content_hash_value=content_hash(page.normalized_url, page.title, page.description or "", preview),
        lang=page.lang,
        category=cls["category"],
        sensitivity=cls["sensitivity"],
        description=page.description or "",
        text_preview=preview,
        clean_markdown=md,
        structured_data=page.structured_data or {},
        site_name=page.site_name,
        http_status=page.http_status,
        fetched_at=page.fetched_at,
        fetch_error=page.fetch_error,
        extraction_engine=page.extraction_engine,
        extraction_status=page.extraction_status,
        extraction_error=page.extraction_error,
        import_batch_id=import_batch_id,
        projects=infer_projects(f"{page.title} {page.normalized_url} {page.description or ''}"),
    )
