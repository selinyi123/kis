"""Ingest GitHub Stars -> KnowledgeCard -> SQLite -> Obsidian notes.

The v0.1 reference connector. Reuses the authenticated `gh` CLI (keyring), so no
token handling lives in this repo — same approach as ClipVault.

Usage (PowerShell):
    python scripts/ingest_github_stars.py
    python scripts/ingest_github_stars.py --user selinyi123 --limit 50
    python scripts/ingest_github_stars.py --db data/kis.db --obsidian-out vault_out
    python scripts/ingest_github_stars.py --no-obsidian        # SQLite only

By default Obsidian notes go to a local ./vault_out (gitignored). Point
--obsidian-out at your real vault (e.g. "D:\\TOOL\\OBSIDIAN\\Home\\prompt仓库\\KIS")
only when you want them written there.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

from kis.card import github_star_card  # noqa: E402
from kis.obsidian import export_card  # noqa: E402
from kis.store import Store  # noqa: E402
from kis.validate import assert_valid, load_schema, validate_card  # noqa: E402

_GH_FALLBACKS = [
    r"C:\Program Files\GitHub CLI\gh.exe",
    r"C:\Program Files (x86)\GitHub CLI\gh.exe",
]


def find_gh() -> str:
    found = shutil.which("gh")
    if found:
        return found
    for cand in _GH_FALLBACKS:
        if os.path.exists(cand):
            return cand
    sys.exit("error: GitHub CLI 'gh' not found on PATH or default install dirs. Install it or run `gh auth login`.")


def resolve_user(gh: str, user: str | None) -> str:
    if user:
        return user
    out = subprocess.run([gh, "api", "user", "--jq", ".login"], capture_output=True, text=True)
    if out.returncode != 0:
        sys.exit(f"error: could not resolve current gh user. Is gh authenticated?\n{out.stderr}")
    return out.stdout.strip()


def fetch_stars(gh: str, user: str, limit: int | None) -> list[dict]:
    """Fetch starred repos via gh with pagination. Topics requested via header."""
    cmd = [
        gh, "api", "--paginate",
        "-H", "Accept: application/vnd.github.star+json",
        f"users/{user}/starred?per_page=100",
    ]
    out = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
    if out.returncode != 0:
        sys.exit(f"error: gh api failed:\n{out.stderr}")
    repos: list[dict] = []
    # --paginate concatenates JSON arrays; handle both array and starred-wrapper.
    for chunk in _iter_json_arrays(out.stdout):
        for item in chunk:
            repo = item.get("repo", item)  # star+json wraps repo under "repo"
            repos.append(repo)
    if limit:
        repos = repos[:limit]
    return repos


def _iter_json_arrays(text: str):
    """Yield each top-level JSON array from gh --paginate output."""
    decoder = json.JSONDecoder()
    idx = 0
    n = len(text)
    while idx < n:
        while idx < n and text[idx] in " \t\r\n":
            idx += 1
        if idx >= n:
            break
        obj, end = decoder.raw_decode(text, idx)
        yield obj
        idx = end


def main() -> int:
    ap = argparse.ArgumentParser(description="Ingest GitHub Stars into KIS.")
    ap.add_argument("--user", default=None, help="GitHub user (default: authenticated gh user)")
    ap.add_argument("--db", default="data/kis.db", help="SQLite path (default: data/kis.db)")
    ap.add_argument("--obsidian-out", default="vault_out", help="Obsidian export dir (default: ./vault_out)")
    ap.add_argument("--limit", type=int, default=None, help="Max repos to ingest")
    ap.add_argument("--no-obsidian", action="store_true", help="Skip Obsidian export")
    args = ap.parse_args()

    gh = find_gh()
    user = resolve_user(gh, args.user)
    print(f"[kis] fetching stars for: {user}")
    repos = fetch_stars(gh, user, args.limit)
    print(f"[kis] fetched {len(repos)} starred repos")

    os.makedirs(os.path.dirname(os.path.abspath(args.db)), exist_ok=True)
    schema = load_schema()
    store = Store(args.db)

    stats = {"inserted": 0, "updated": 0, "unchanged": 0, "invalid": 0, "exported": 0}
    for repo in repos:
        card = github_star_card(repo)
        errors = validate_card(card, schema)
        if errors:
            stats["invalid"] += 1
            print(f"  ! invalid card for {repo.get('full_name')}: {errors[0]}")
            continue
        status = store.upsert(card)
        stats[status] += 1
        if not args.no_obsidian:
            export_card(card, args.obsidian_out, rel_dir="GitHub-Stars")
            stats["exported"] += 1

    store.close()
    print("[kis] done:")
    print(f"      inserted={stats['inserted']} updated={stats['updated']} "
          f"unchanged={stats['unchanged']} invalid={stats['invalid']} exported={stats['exported']}")
    print(f"      db={args.db}  total_cards_in_db={Store(args.db).count()}")
    if not args.no_obsidian:
        print(f"      obsidian notes -> {os.path.abspath(args.obsidian_out)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
