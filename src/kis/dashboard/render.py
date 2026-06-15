"""Markdown rendering for the review dashboard (KIS-015). Pure, deterministic.

Safety: table pipes are escaped; missing derived -> 'unknown'; missing review ->
'pending'; suggested commands are fenced and always include --card-id/--reason.
"""

from __future__ import annotations

from typing import Any, Callable

from ..obsidian import _slug as card_slug
from . import GENERATOR_VERSION
from . import commands as cmds
from .models import (
    PAGE_ARCHIVE, PAGE_CANONICAL, PAGE_DEFERRED, PAGE_INBOX, PAGE_REJECTED, PAGE_STATS,
)
from .stats import compute_review_stats


def _esc(text: Any) -> str:
    return str(text if text is not None else "").replace("|", "\\|").replace("\n", " ").strip()


def _header(title: str, generated_at: str) -> list[str]:
    return [
        "---",
        f"generated_at: {generated_at}",
        f"generator: {GENERATOR_VERSION}",
        "kind: kis-review-dashboard",
        "---",
        "",
        f"# {title}",
        "",
        "> 只读看板（KIS-015）。状态变更请用 `scripts/review_cards.py`；此页不自动执行任何命令。",
        "",
    ]


def _relevance_str(card: dict[str, Any]) -> str:
    rel = card.get("derived", {}).get("project_relevance")
    if not rel:
        return "unknown"
    hot = [f"{k}:{v}" for k, v in rel.items() if v and v > 0]
    return ", ".join(hot) if hot else "—"


def _link(card: dict[str, Any]) -> str:
    title = card["content"].get("title", card["id"])
    return f"[[{card_slug(title)}\\|{_esc(title)}]]"


def _card_block(card: dict[str, Any], command_fn: Callable[[dict[str, Any]], list[str]]) -> list[str]:
    d = card.get("derived", {})
    review = card.get("review")
    out = [
        f"## {_esc(card['content'].get('title', card['id']))}",
        "",
        f"{_link(card)}",
        "",
        "| Field | Value |", "|---|---|",
        f"| Card ID | {card['id']} |",
        f"| Source Type | {_esc(card['source'].get('source_type'))} |",
        f"| Category | {_esc(card['enrichment'].get('category') or 'unknown')} |",
        f"| Value Level | {_esc(d.get('value_level', 'unknown'))} |",
        f"| Next Action | {_esc(d.get('next_action', 'unknown'))} |",
        f"| Project Relevance | {_esc(_relevance_str(card))} |",
        f"| Lifecycle | {_esc(card['lifecycle'].get('state', 'inbox'))} |",
        f"| Review | {_esc(review.get('decision') if review else 'pending')} |",
        f"| Source Hash | {_esc(card.get('content_hash', ''))[:16]} |",
        f"| Derived Hash | {_esc((review or {}).get('derived_hash', '—'))} |",
        "",
        "### Summary",
        _esc(d.get("ai_summary")) or "unknown",
        "",
    ]
    commands = command_fn(card)
    if commands:
        out += ["### Suggested Commands", "", "```bash", *commands, "```", ""]
    return out


def _queue_page(title: str, cards: list[dict[str, Any]], command_fn, generated_at: str) -> str:
    out = _header(title, generated_at)
    out.append(f"**{len(cards)} card(s).**\n")
    if not cards:
        out.append("_(empty)_")
    for c in cards:
        out += _card_block(c, command_fn)
    return "\n".join(out)


def render_inbox(cards, generated_at):
    return _queue_page("Review Inbox", cards, cmds.inbox_commands, generated_at)


def render_canonical(cards, generated_at):
    return _queue_page("Canonical Candidates", cards, cmds.canonical_commands, generated_at)


def render_archive(cards, generated_at):
    return _queue_page("Archive Candidates", cards, cmds.archive_commands, generated_at)


def render_deferred(cards, generated_at):
    return _queue_page("Deferred Queue", cards, cmds.deferred_commands, generated_at)


def render_rejected(cards, generated_at):
    return _queue_page("Rejected Queue", cards, cmds.rejected_commands, generated_at)


def _counter_table(title: str, counts: dict[str, int]) -> list[str]:
    out = [f"### {title}", "", "| Key | Count |", "|---|---:|"]
    for k, v in sorted(counts.items(), key=lambda kv: (-kv[1], kv[0])):
        out.append(f"| {_esc(k)} | {v} |")
    out.append("")
    return out


def render_stats(stats: dict[str, Any], generated_at: str, last_ingest: dict[str, Any] | None = None) -> str:
    out = _header("Review Stats", generated_at)
    out.append(f"**Total Cards: {stats.get('total', 0)}**\n")
    out += _counter_table("By Lifecycle", stats["by_lifecycle"])
    out += _counter_table("By Source Type", stats["by_source_type"])
    out += _counter_table("By Category", stats["by_category"])
    out += _counter_table("By Value Level", stats["by_value_level"])
    out += _counter_table("By Next Action", stats["by_next_action"])
    out += _counter_table("By Project Relevance", stats["by_project_relevance"])
    out += _counter_table("By Sensitivity", stats["by_sensitivity"])
    out += _counter_table("By Generated Day", stats["by_generated_day"])
    ext = stats.get("external_inbox", {})
    out.append(f"### External Inbox (total {ext.get('total', 0)})\n")
    out += _counter_table("External Inbox by Source Type", ext.get("by_source_type", {}))
    out += _counter_table("External Inbox by Project", ext.get("by_project", {}))
    if last_ingest:
        out += ["### Last Ingest Run", "", "| Metric | Count |", "|---|---:|",
                f"| source_type | {last_ingest.get('source_type', '-')} |",
                f"| created | {last_ingest.get('created', 0)} |",
                f"| skipped_duplicate | {last_ingest.get('skipped_duplicate', 0)} |",
                f"| blocked | {last_ingest.get('blocked', 0)} |",
                f"| errors | {last_ingest.get('errors', 0)} |", ""]
    return "\n".join(out)


def render_overview(cards: list[dict[str, Any]], counts: dict[str, int],
                    candidate_counts: dict[str, int], generated_at: str) -> str:
    out = _header("KIS Review Dashboard", generated_at)
    out += [
        "## Summary", "", "| Metric | Count |", "|---|---:|",
        f"| Total Cards | {len(cards)} |",
        f"| Inbox | {counts.get('inbox', 0)} |",
        f"| Reviewed | {counts.get('reviewed', 0)} |",
        f"| Canonical | {counts.get('canonical', 0)} |",
        f"| Archived | {counts.get('archived', 0)} |",
        f"| Deferred | {counts.get('deferred', 0)} |",
        f"| Rejected | {counts.get('rejected', 0)} |",
        "",
        "## Priority Queues", "",
        f"- Hot + Integrate: {candidate_counts.get('hot_integrate', 0)}",
        f"- Critical: {candidate_counts.get('critical', 0)}",
        f"- Needs Review (Inbox): {counts.get('inbox', 0)}",
        f"- Canonical Candidates: {candidate_counts.get('canonical', 0)}",
        f"- Archive Candidates: {candidate_counts.get('archive', 0)}",
        f"- External Inbox: {candidate_counts.get('external_inbox', 0)}",
        f"- Deferred: {counts.get('deferred', 0)}",
        f"- Rejected: {counts.get('rejected', 0)}",
        "",
        "## Links", "",
        f"- [[{PAGE_INBOX[:-3]}]]",
        f"- [[{PAGE_CANONICAL[:-3]}]]",
        f"- [[{PAGE_ARCHIVE[:-3]}]]",
        f"- [[{PAGE_DEFERRED[:-3]}]]",
        f"- [[{PAGE_REJECTED[:-3]}]]",
        f"- [[{PAGE_STATS[:-3]}]]",
        "",
    ]
    return "\n".join(out)


__all__ = ["render_inbox", "render_canonical", "render_archive", "render_deferred",
           "render_rejected", "render_stats", "render_overview", "compute_review_stats"]
