"""KIS-018 External Inbox Ingestion CLI.

Ingest already-EXPORTED external material (no network) into the inbox:
    github-stars (JSON/MD) · bookmarks (HTML) · web-clips (JSONL)

All new cards land in lifecycle.state=inbox; secret-bearing items are blocked;
duplicates are skipped; dry-run previews identical counts. Review via KIS-014.

Usage (PowerShell):
    python scripts/ingest_external.py github-stars --input exports/stars.json --dry-run
    python scripts/ingest_external.py bookmarks --input exports/bookmarks.html
    python scripts/ingest_external.py web-clips --input exports/clips.jsonl
    python scripts/ingest_external.py report
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

from kis.ingest import runner  # noqa: E402
from kis.ingest.report import render_markdown  # noqa: E402
from kis.store import Store  # noqa: E402

_REPORT_DIR = os.path.join("data", "ingest_reports")
_LATEST = os.path.join(_REPORT_DIR, "latest.json")


def _summary(rep) -> None:
    d = rep.to_dict()
    print(f"[kis] ingest {d['source_type']} ({'dry-run' if d['dry_run'] else 'real'}): "
          f"seen={d['total_seen']} created={d['created']} updated={d['updated']} "
          f"skipped_duplicate={d['skipped_duplicate']} blocked={d['blocked']} errors={d['errors']}")


def cmd_ingest(source: str, args) -> int:
    if not os.path.exists(args.input):
        sys.exit(f"error: input not found: {args.input}")
    store = Store(args.db_path)
    out = None if (args.dry_run or args.no_obsidian) else args.obsidian_dir
    rep = runner.ingest(source, args.input, store, out, dry_run=args.dry_run, limit=args.limit,
                        source_project=args.source_project, category=args.category, force=args.force)
    store.close()
    _summary(rep)
    if not args.dry_run:
        os.makedirs(_REPORT_DIR, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d-%H%M%S")
        base = os.path.join(_REPORT_DIR, f"{rep.source_type}_{ts}")
        rp = args.report_path or (base + ".json")
        with open(rp, "w", encoding="utf-8") as fh:
            json.dump(rep.to_dict(), fh, ensure_ascii=False, indent=2)
        with open(base + ".md", "w", encoding="utf-8") as fh:
            fh.write(render_markdown(rep))
        with open(_LATEST, "w", encoding="utf-8") as fh:
            json.dump(rep.to_dict(), fh, ensure_ascii=False, indent=2)
        print(f"      report -> {rp}  (+ {base}.md)")
    return 0 if rep.errors == 0 else 1


def cmd_report(args) -> int:
    if not os.path.exists(_LATEST):
        print("[kis] no ingest report yet."); return 0
    with open(_LATEST, encoding="utf-8") as fh:
        d = json.load(fh)
    print(f"[kis] latest ingest: {d['source_type']} seen={d['total_seen']} created={d['created']} "
          f"updated={d['updated']} skipped_duplicate={d['skipped_duplicate']} "
          f"blocked={d['blocked']} errors={d['errors']}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="KIS-018 external inbox ingestion.")
    sub = ap.add_subparsers(dest="command", required=True)
    for name in ("github-stars", "bookmarks", "web-clips"):
        p = sub.add_parser(name)
        p.add_argument("--input", required=True)
        p.add_argument("--db-path", dest="db_path", default="data/kis.db")
        p.add_argument("--obsidian-dir", dest="obsidian_dir", default="vault_out")
        p.add_argument("--no-obsidian", action="store_true")
        p.add_argument("--dry-run", action="store_true")
        p.add_argument("--limit", type=int, default=None)
        p.add_argument("--source-project", dest="source_project", default=None)
        p.add_argument("--category", default=None)
        p.add_argument("--force", action="store_true")
        p.add_argument("--report-path", dest="report_path", default=None)
    sub.add_parser("report")
    return ap


def main() -> int:
    args = build_parser().parse_args()
    if args.command == "report":
        return cmd_report(args)
    return cmd_ingest(args.command, args)


if __name__ == "__main__":
    raise SystemExit(main())
