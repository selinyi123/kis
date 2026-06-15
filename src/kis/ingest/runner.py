"""External ingestion orchestrator (KIS-018).

parse -> build card -> secret/sensitivity guard -> dedupe -> store(inbox) ->
Obsidian External-Inbox. dry_run computes identical counts without writing.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from ..obsidian import export_card, render_external_inbox_md
from ..validate import load_schema, validate_card
from . import INBOX_FOLDER, SOURCE_TYPE
from . import bookmarks as p_bookmarks
from . import github_stars as p_github
from . import web_clips as p_web
from .dedupe import Deduper
from .models import IngestReport
from .normalizer import build_card
from .safety import is_blocked

_PARSERS = {"github-stars": p_github.parse, "bookmarks": p_bookmarks.parse, "web-clips": p_web.parse}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def ingest(source: str, input_path: str, store: Any, obsidian_dir: str | None,
           dry_run: bool = False, limit: int | None = None,
           source_project: str | None = None, category: str | None = None,
           force: bool = False) -> IngestReport:
    if source not in SOURCE_TYPE:
        raise ValueError(f"unknown source: {source}")
    st = SOURCE_TYPE[source]
    rep = IngestReport(source_type=st, input_file=input_path, started_at=_now(), dry_run=dry_run)
    schema = load_schema()
    dedup = Deduper(store)

    items = _PARSERS[source](input_path)
    if limit:
        items = items[:limit]

    for raw in items:
        rep.total_seen += 1
        if isinstance(raw, dict) and raw.get("_parse_error"):
            rep.errors += 1
            rep.error_items.append({"reason": raw["_parse_error"]})
            continue
        try:
            card = build_card(st, raw, source_project, category)
        except Exception as e:  # malformed / missing url etc.
            rep.errors += 1
            rep.error_items.append({"reason": str(e), "raw": str(raw)[:160]})
            continue

        title = card["content"]["title"]
        body = card["content"]["body_md"]
        preview = card["content"].get("text_preview", "")
        blocked, reason = is_blocked(title, body, preview)
        if blocked or card["safety"].get("sensitivity") == "blocked":
            rep.blocked += 1
            rep.blocked_items.append({"url": card["source"]["url"],
                                      "reason": reason or "sensitivity:blocked"})
            continue

        if dedup.status(card) == "duplicate" and not force:
            rep.skipped_duplicate += 1
            rep.duplicates.append({"url": card["source"]["url"], "id": card["id"]})
            continue

        errs = validate_card(card, schema)
        if errs:
            rep.errors += 1
            rep.error_items.append({"reason": f"schema: {errs[0]}", "url": card["source"]["url"]})
            continue

        rep.created_cards.append({"id": card["id"], "title": title, "url": card["source"]["url"]})
        if dry_run:
            rep.created += 1
            continue
        status = store.upsert(card)
        if status == "updated":
            rep.updated += 1
        else:
            rep.created += 1
        if obsidian_dir:
            export_card(card, obsidian_dir, rel_dir=f"External-Inbox/{INBOX_FOLDER[st]}",
                        renderer=render_external_inbox_md)

    rep.finished_at = _now()
    return rep
