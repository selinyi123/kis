"""Human review queue CLI (KIS-014).

canonical is produced ONLY by an explicit `approve` command. Review writes only
lifecycle + review; the factual core is immutable. All write ops support
--dry-run and are idempotent. Fully offline.

Usage (PowerShell):
    python scripts/review_cards.py list --status inbox
    python scripts/review_cards.py list --value-level hot --next-action integrate
    python scripts/review_cards.py show --card-id <id>
    python scripts/review_cards.py mark-reviewed --card-id <id> --reason "verified source"
    python scripts/review_cards.py approve --card-id <id> --reason "promote after review"
    python scripts/review_cards.py archive --card-id <id> --reason "low relevance"
    python scripts/review_cards.py defer  --card-id <id> --reason "revisit later"
    python scripts/review_cards.py reject --card-id <id> --reason "not useful"
    python scripts/review_cards.py export --status canonical --format md
"""

from __future__ import annotations

import argparse
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

from kis.classify import folder_for_category  # noqa: E402
from kis.obsidian import export_card, render_bookmark_md, render_card_md, render_webclip_md  # noqa: E402
from kis.review import COMMAND_TO_DECISION, apply_review  # noqa: E402
from kis.review.export import export_queue  # noqa: E402
from kis.review.queue import filter_cards, queue_counts  # noqa: E402
from kis.store import Store  # noqa: E402
from kis.validate import load_schema, validate_card  # noqa: E402

_WRITE_COMMANDS = set(COMMAND_TO_DECISION)


def _rel_dir(card):
    st = card["source"]["source_type"]
    cat = card["enrichment"].get("category", "")
    if st == "github_star":
        return "GitHub-Stars", render_card_md
    if st == "web_bookmark":
        return f"Browser-Bookmarks/{folder_for_category(cat)}", render_bookmark_md
    if st == "web_clip":
        return f"Web-Clips/{folder_for_category(cat)}", render_webclip_md
    return st, render_card_md


def _filters(args):
    return dict(status=getattr(args, "status", None), value_level=getattr(args, "value_level", None),
                next_action=getattr(args, "next_action", None), source_type=getattr(args, "source_type", None),
                category=getattr(args, "category", None))


def cmd_list(store, args) -> int:
    cards = filter_cards(store.all_cards(), **_filters(args))
    if args.limit:
        cards = cards[: args.limit]
    print(f"{'ID':18} {'STATUS':10} {'VALUE':9} {'NEXT':10} TITLE")
    for c in cards:
        d = c.get("derived", {})
        print(f"{c['id']:18} {c['lifecycle'].get('state', ''):10} "
              f"{d.get('value_level', '-'):9} {d.get('next_action', '-'):10} {c['content'].get('title', '')[:48]}")
    print(f"\n[kis] {len(cards)} card(s). queue={queue_counts(store.all_cards())}")
    return 0


def cmd_show(store, args) -> int:
    c = store.get_card(args.card_id)
    if not c:
        print(f"not found: {args.card_id}"); return 1
    d, r = c.get("derived", {}), c.get("review")
    print(f"id: {c['id']}\nstatus: {c['lifecycle'].get('state')}\ntitle: {c['content'].get('title')}")
    print(f"source_type: {c['source'].get('source_type')}  category: {c['enrichment'].get('category')}")
    print(f"value_level: {d.get('value_level')}  next_action: {d.get('next_action')}")
    print(f"review: {r if r else 'pending'}")
    return 0


def cmd_export(store, args) -> int:
    cards = filter_cards(store.all_cards(), **_filters(args))
    print(export_queue(cards, fmt=args.format))
    return 0


def cmd_write(store, args, schema) -> int:
    decision = COMMAND_TO_DECISION[args.command]
    card = store.get_card(args.card_id)
    if not card:
        print(f"not found: {args.card_id}"); return 1
    try:
        new_card, changed = apply_review(card, decision, args.reason, reviewer=args.reviewer)
    except Exception as e:
        print(f"[kis] review refused: {e}"); return 1
    if not changed:
        print(f"[kis] no-op (already {card['lifecycle'].get('state')}) — idempotent"); return 0
    errors = validate_card(new_card, schema)
    if errors:
        print(f"[kis] invalid after review: {errors[0]}"); return 1
    if args.dry_run:
        print(f"[kis] DRY-RUN {decision}: {card['lifecycle'].get('state')} -> {new_card['lifecycle']['state']} "
              f"(review_hash={new_card['review']['review_hash']}) — not saved")
        return 0
    store.save_review(new_card)
    if not args.no_obsidian and args.obsidian_dir:
        rel, renderer = _rel_dir(new_card)
        export_card(new_card, args.obsidian_dir, rel_dir=rel, renderer=renderer)
    print(f"[kis] {decision}: {new_card['review']['previous_status']} -> {new_card['review']['next_status']} "
          f"({new_card['id']})")
    return 0


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="KIS-014 human review queue.")
    ap.add_argument("--db-path", default="data/kis.db")
    ap.add_argument("--obsidian-dir", default="vault_out")
    ap.add_argument("--no-obsidian", action="store_true")
    sub = ap.add_subparsers(dest="command", required=True)

    def add_filters(p):
        p.add_argument("--status")
        p.add_argument("--value-level", dest="value_level")
        p.add_argument("--next-action", dest="next_action")
        p.add_argument("--source-type", dest="source_type")
        p.add_argument("--category")
        p.add_argument("--limit", type=int, default=None)

    add_filters(sub.add_parser("list"))
    sp = sub.add_parser("export"); add_filters(sp); sp.add_argument("--format", choices=["md", "json"], default="md")
    sub.add_parser("show").add_argument("--card-id", required=True)
    for cmd in COMMAND_TO_DECISION:
        p = sub.add_parser(cmd)
        p.add_argument("--card-id", required=True)
        p.add_argument("--reason", required=True)
        p.add_argument("--reviewer", default="human")
        p.add_argument("--dry-run", action="store_true")
        p.add_argument("--limit", type=int, default=None)
    return ap


def main() -> int:
    args = build_parser().parse_args()
    store = Store(args.db_path)
    try:
        if args.command == "list":
            return cmd_list(store, args)
        if args.command == "show":
            return cmd_show(store, args)
        if args.command == "export":
            return cmd_export(store, args)
        if args.command in _WRITE_COMMANDS:
            return cmd_write(store, args, load_schema())
        print(f"unknown command: {args.command}"); return 2
    finally:
        store.close()


if __name__ == "__main__":
    raise SystemExit(main())
