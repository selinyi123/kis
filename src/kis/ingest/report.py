"""Render the ingestion report (KIS-018)."""

from __future__ import annotations

from .models import IngestReport


def _esc(s: str) -> str:
    return str(s or "").replace("|", "\\|").replace("\n", " ")


def render_markdown(rep: IngestReport) -> str:
    out = [
        "# KIS-018 Ingestion Report", "",
        f"_source_type: {rep.source_type} · input: {_esc(rep.input_file)} · "
        f"dry_run: {rep.dry_run} · {rep.started_at} → {rep.finished_at}_", "",
        "## Summary", "", "| Metric | Count |", "|---|---:|",
        f"| total_seen | {rep.total_seen} |",
        f"| created | {rep.created} |",
        f"| updated | {rep.updated} |",
        f"| skipped_duplicate | {rep.skipped_duplicate} |",
        f"| blocked | {rep.blocked} |",
        f"| errors | {rep.errors} |",
        "",
        "## Created Cards", "",
    ]
    out += ([f"- {c['id']} — {_esc(c['title'])} ({_esc(c['url'])})" for c in rep.created_cards[:100]]
            or ["_(none)_"])
    out += ["", "## Duplicates", ""]
    out += ([f"- {_esc(d.get('url'))}" for d in rep.duplicates[:100]] or ["_(none)_"])
    out += ["", "## Blocked", ""]
    out += ([f"- {_esc(b.get('url'))} — {_esc(b.get('reason'))}" for b in rep.blocked_items[:100]] or ["_(none)_"])
    out += ["", "## Errors", ""]
    out += ([f"- {_esc(e.get('reason'))}" for e in rep.error_items[:100]] or ["_(none)_"])
    out += ["", "## Next Review Actions", "",
            "New cards are in `inbox`. Review them with `scripts/review_cards.py` "
            "(mark-reviewed / archive / defer / reject) — never auto-approved.", ""]
    return "\n".join(out)
