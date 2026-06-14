"""Ingest a Netscape bookmark HTML export -> KnowledgeCard -> SQLite -> Obsidian.

The v0.2a second source. Blocked bookmarks (adult / proxy-airport / tax-free
address / anti-detect) never enter SQLite or Obsidian — they are appended to a
blocked JSONL log only.

Usage (PowerShell):
    python scripts/ingest_bookmarks.py "C:\\Users\\Administrator\\Documents\\bookmarks_2026_6_14.html"
    python scripts/ingest_bookmarks.py bookmarks.html --db data/kis.db --obsidian-out vault_out
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

from kis.card import now_iso  # noqa: E402
from kis.classify import classify_bookmark  # noqa: E402
from kis.connectors.bookmarks import bookmark_to_card, parse_bookmarks_html  # noqa: E402
from kis.obsidian import export_card, render_bookmark_md  # noqa: E402
from kis.store import Store  # noqa: E402
from kis.validate import load_schema, validate_card  # noqa: E402


def ingest_bookmarks(path: str, db: str, obsidian_out: str | None, batch_id: str | None = None) -> dict:
    """Reusable pipeline. Returns stats dict. obsidian_out=None skips export."""
    batch_id = batch_id or "bm_" + datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    schema = load_schema()
    items = parse_bookmarks_html(path)

    os.makedirs(os.path.dirname(os.path.abspath(db)), exist_ok=True)
    store = Store(db)
    stats = {"parsed": len(items), "inserted": 0, "updated": 0, "unchanged": 0,
             "blocked": 0, "invalid": 0, "exported": 0}

    blocked_records = []
    for item in items:
        cls = classify_bookmark(item.title, item.url, item.folder_path)
        if cls["decision"] == "blocked":
            stats["blocked"] += 1
            blocked_records.append({
                "ts": now_iso(), "title": item.title, "url": item.url,
                "folder_path": item.folder_path, "reason": cls["category"],
                "import_batch_id": batch_id,
            })
            continue

        card = bookmark_to_card(item, import_batch_id=batch_id)
        errors = validate_card(card, schema)
        if errors:
            stats["invalid"] += 1
            print(f"  ! invalid card for {item.url}: {errors[0]}")
            continue

        status = store.upsert(card)
        stats[status] += 1
        if obsidian_out and status != "unchanged":
            rel = f"Browser-Bookmarks/{cls['folder']}"
            export_card(card, obsidian_out, rel_dir=rel, renderer=render_bookmark_md)
            stats["exported"] += 1

    # blocked log (JSONL), never into Obsidian general dirs
    if blocked_records and obsidian_out:
        blocked_dir = os.path.join(obsidian_out, "_blocked")
        os.makedirs(blocked_dir, exist_ok=True)
        log_path = os.path.join(blocked_dir, f"blocked-bookmarks-{datetime.now().strftime('%Y%m%d')}.jsonl")
        with open(log_path, "a", encoding="utf-8") as fh:
            for rec in blocked_records:
                fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
        stats["blocked_log"] = log_path

    store.close()
    return stats


def main() -> int:
    ap = argparse.ArgumentParser(description="Ingest a Netscape bookmark HTML export into KIS.")
    ap.add_argument("path", help="Path to bookmarks .html")
    ap.add_argument("--db", default="data/kis.db")
    ap.add_argument("--obsidian-out", default="vault_out")
    ap.add_argument("--no-obsidian", action="store_true")
    args = ap.parse_args()

    if not os.path.exists(args.path):
        sys.exit(f"error: file not found: {args.path}")

    out = None if args.no_obsidian else args.obsidian_out
    stats = ingest_bookmarks(args.path, args.db, out)
    print("[kis] bookmarks done:")
    print(f"      parsed={stats['parsed']} inserted={stats['inserted']} updated={stats['updated']} "
          f"unchanged={stats['unchanged']} blocked={stats['blocked']} invalid={stats['invalid']} "
          f"exported={stats['exported']}")
    print(f"      db={args.db}  web_bookmark_cards={Store(args.db).count('web_bookmark')}")
    if out:
        print(f"      obsidian notes -> {os.path.abspath(out)}/Browser-Bookmarks/")
        if stats.get("blocked_log"):
            print(f"      blocked log    -> {stats['blocked_log']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
