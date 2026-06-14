"""Pluggable web-page extraction backends (KIS-009).

The stdlib backend is the always-available baseline. Crawl4AI is an *optional*
enhancement: it is never imported at module top level, never a hard dependency,
and never replaces the baseline. Selection and SSRF/blocked gating live in
``scripts/ingest_url.py`` (KIS-008) — extractors only transform an already
validated URL into an ``ExtractedPage``.
"""
