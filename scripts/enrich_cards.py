"""Enrich KnowledgeCards with the derived AI layer (KIS-013).

Derived layer rules (see docs/KIS-013_PROMPT_INJECTION_BOUNDARY.md):
  * writes ONLY card['derived'] — never source/content/enrichment;
  * blocked cards are skipped;
  * heuristic mode is fully offline; LLM is optional;
  * every result keeps reproducible generator metadata.

Usage (PowerShell):
    python scripts/enrich_cards.py --mode heuristic
    python scripts/enrich_cards.py --mode auto --provider mock --limit 10
    python scripts/enrich_cards.py --mode llm --provider openai --source-type web_clip
    python scripts/enrich_cards.py --mode heuristic --dry-run
"""

from __future__ import annotations

import argparse
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

from kis.classify import folder_for_category  # noqa: E402
from kis.enrich.heuristic import enrich_card  # noqa: E402
from kis.enrich.providers import get_provider  # noqa: E402
from kis.obsidian import export_card, render_bookmark_md, render_card_md, render_webclip_md  # noqa: E402
from kis.store import Store  # noqa: E402
from kis.validate import load_schema, validate_card  # noqa: E402

_DONE = {"heuristic", "llm_generated"}


def _rel_dir(card: dict) -> tuple[str, callable]:
    st = card["source"]["source_type"]
    cat = card["enrichment"].get("category", "")
    if st == "github_star":
        return "GitHub-Stars", render_card_md
    if st == "web_bookmark":
        return f"Browser-Bookmarks/{folder_for_category(cat)}", render_bookmark_md
    if st == "web_clip":
        return f"Web-Clips/{folder_for_category(cat)}", render_webclip_md
    return st, render_card_md


def enrich_db(db_path: str, vault_path: str | None, mode: str = "heuristic", provider=None,
              limit: int | None = None, dry_run: bool = False, force: bool = False,
              source_type: str | None = None, category: str | None = None) -> dict:
    schema = load_schema()
    store = Store(db_path)
    stats = {"processed": 0, "updated": 0, "skipped_blocked": 0, "skipped_done": 0,
             "errors": 0, "mode": mode, "dry_run": dry_run}

    for card in store.all_cards():
        if source_type and card["source"]["source_type"] != source_type:
            continue
        if category and card["enrichment"].get("category") != category:
            continue
        if card["safety"].get("sensitivity") == "blocked":
            stats["skipped_blocked"] += 1
            continue
        existing = card.get("derived", {}).get("processing_status")
        if existing in _DONE and not force:
            stats["skipped_done"] += 1
            continue

        stats["processed"] += 1
        try:
            enriched = enrich_card(card, mode=mode, provider=provider)
        except Exception as e:  # forced-LLM failure etc. -> mark failed, never fake success
            stats["errors"] += 1
            print(f"  ! enrich failed for {card['id']}: {e}")
            continue
        if enriched is None:
            stats["skipped_blocked"] += 1
            continue
        if validate_card(enriched, schema):
            stats["errors"] += 1
            print(f"  ! invalid derived for {card['id']}: {validate_card(enriched, schema)[0]}")
            continue
        if dry_run:
            continue
        store.save_enrichment(enriched)
        stats["updated"] += 1
        if vault_path:
            rel, renderer = _rel_dir(enriched)
            export_card(enriched, vault_path, rel_dir=rel, renderer=renderer)

        if limit and stats["processed"] >= limit:
            break

    store.close()
    return stats


def main() -> int:
    ap = argparse.ArgumentParser(description="Enrich KnowledgeCards (derived layer).")
    ap.add_argument("--db", default="data/kis.db")
    ap.add_argument("--vault", default="vault_out")
    ap.add_argument("--mode", choices=["heuristic", "llm", "auto"], default="heuristic")
    ap.add_argument("--provider", choices=["none", "mock", "openai"], default="none")
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--source-type", choices=["github_star", "web_bookmark", "web_clip"], default=None)
    ap.add_argument("--category", default=None)
    ap.add_argument("--no-obsidian", action="store_true")
    args = ap.parse_args()

    provider = get_provider(args.provider)
    if args.mode == "llm" and provider is None:
        sys.exit("error: --mode llm requires --provider mock|openai")

    vault = None if (args.no_obsidian or args.dry_run) else args.vault
    stats = enrich_db(args.db, vault, mode=args.mode, provider=provider, limit=args.limit,
                      dry_run=args.dry_run, force=args.force,
                      source_type=args.source_type, category=args.category)
    print("[kis] enrich done:")
    for k in ("processed", "updated", "skipped_blocked", "skipped_done", "errors", "mode", "dry_run"):
        print(f"      {k}={stats[k]}")
    return 0 if stats["errors"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
