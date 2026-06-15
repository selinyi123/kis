"""Dashboard page model + ranking constants (KIS-015)."""

from __future__ import annotations

from dataclasses import dataclass

# Output filenames (under <obsidian-dir>/Dashboards/)
PAGE_OVERVIEW = "KIS Review Dashboard.md"
PAGE_INBOX = "Review Inbox.md"
PAGE_CANONICAL = "Canonical Candidates.md"
PAGE_ARCHIVE = "Archive Candidates.md"
PAGE_DEFERRED = "Deferred Queue.md"
PAGE_REJECTED = "Rejected Queue.md"
PAGE_STATS = "Review Stats.md"

# --only selectors -> the pages they build
ONLY_MAP = {
    "overview": [PAGE_OVERVIEW],
    "inbox": [PAGE_INBOX],
    "canonical": [PAGE_CANONICAL],
    "archive": [PAGE_ARCHIVE],
    "deferred": [PAGE_DEFERRED],
    "rejected": [PAGE_REJECTED],
    "stats": [PAGE_STATS],
}

# Priority ranks (lower = higher priority)
VALUE_RANK = {"critical": 0, "hot": 1, "warm": 2, "cold": 3}
ACTION_RANK = {"integrate": 0, "test": 1, "read": 2, "monitor": 3, "archive": 4, "ignore": 5}
_UNKNOWN_RANK = 9


@dataclass
class DashboardPage:
    filename: str
    body: str
