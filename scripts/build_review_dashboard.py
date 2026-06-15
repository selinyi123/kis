"""Build the KIS-015 Review Dashboard (read-only Obsidian Markdown boards).

Generates static boards from the card store. NEVER writes the store, never
changes lifecycle/review. Suggested commands are copy-paste only.

Usage (PowerShell):
    python scripts/build_review_dashboard.py
    python scripts/build_review_dashboard.py --obsidian-dir "D:\\TOOL\\OBSIDIAN\\Home\\prompt仓库\\KIS 知识情报系统"
    python scripts/build_review_dashboard.py --dry-run
    python scripts/build_review_dashboard.py --only inbox
    python scripts/build_review_dashboard.py --only stats
"""

from __future__ import annotations

import argparse
import os
import sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

from kis.dashboard import render  # noqa: E402
from kis.dashboard.models import (  # noqa: E402
    ONLY_MAP, PAGE_ARCHIVE, PAGE_CANONICAL, PAGE_DEFERRED, PAGE_INBOX, PAGE_OVERVIEW,
    PAGE_REJECTED, PAGE_STATS,
)
from kis.dashboard.selectors import (  # noqa: E402
    select_archive_candidates, select_canonical_candidates, select_deferred_cards,
    select_inbox_cards, select_rejected_cards,
)
from kis.dashboard.stats import compute_review_stats  # noqa: E402
from kis.review.queue import queue_counts  # noqa: E402
from kis.store import Store  # noqa: E402


def _load_last_ingest():
    import json
    p = os.path.join("data", "ingest_reports", "latest.json")
    if os.path.exists(p):
        try:
            with open(p, encoding="utf-8") as fh:
                return json.load(fh)
        except (OSError, ValueError):
            return None
    return None


def build_pages(cards: list[dict], generated_at: str, only: str | None = None) -> dict[str, str]:
    """Return {filename: body}. Pure given cards + generated_at."""
    counts = queue_counts(cards)
    inbox = select_inbox_cards(cards)
    canonical = select_canonical_candidates(cards)
    archive = select_archive_candidates(cards)
    deferred = select_deferred_cards(cards)
    rejected = select_rejected_cards(cards)
    stats = compute_review_stats(cards)
    candidate_counts = {
        "canonical": len(canonical), "archive": len(archive),
        "external_inbox": stats.get("external_inbox", {}).get("total", 0),
        "hot_integrate": sum(1 for c in cards if c.get("derived", {}).get("value_level") == "hot"
                             and c.get("derived", {}).get("next_action") == "integrate"),
        "critical": stats["by_value_level"].get("critical", 0),
    }
    last_ingest = _load_last_ingest()

    pages = {
        PAGE_OVERVIEW: render.render_overview(cards, counts, candidate_counts, generated_at),
        PAGE_INBOX: render.render_inbox(inbox, generated_at),
        PAGE_CANONICAL: render.render_canonical(canonical, generated_at),
        PAGE_ARCHIVE: render.render_archive(archive, generated_at),
        PAGE_DEFERRED: render.render_deferred(deferred, generated_at),
        PAGE_REJECTED: render.render_rejected(rejected, generated_at),
        PAGE_STATS: render.render_stats(stats, generated_at, last_ingest),
    }
    if only:
        wanted = set(ONLY_MAP.get(only, []))
        pages = {k: v for k, v in pages.items() if k in wanted}
    return pages


def main() -> int:
    ap = argparse.ArgumentParser(description="Build the KIS review dashboard (read-only).")
    ap.add_argument("--db-path", default="data/kis.db")
    ap.add_argument("--obsidian-dir", default="vault_out")
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--only", choices=list(ONLY_MAP), default=None)
    args = ap.parse_args()

    store = Store(args.db_path)
    cards = store.load_dashboard_cards(limit=args.limit)
    store.close()  # read-only; closed before any writes

    generated_at = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    pages = build_pages(cards, generated_at, only=args.only)
    out_dir = os.path.join(args.obsidian_dir, "Dashboards")

    print(f"[kis] dashboard: cards={len(cards)} pages={len(pages)} -> {out_dir}")
    counts = queue_counts(cards)
    print(f"      queue={counts}")
    if args.dry_run:
        print("      DRY-RUN (no files written):")
        for fn in pages:
            print(f"        - {os.path.join(out_dir, fn)}")
        return 0

    os.makedirs(out_dir, exist_ok=True)
    for fn, body in pages.items():
        with open(os.path.join(out_dir, fn), "w", encoding="utf-8") as fh:
            fh.write(body)
        print(f"      wrote {fn}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
