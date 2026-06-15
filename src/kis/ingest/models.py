"""Ingestion data structures (KIS-018)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class IngestReport:
    source_type: str
    input_file: str
    started_at: str = ""
    finished_at: str = ""
    total_seen: int = 0
    created: int = 0
    updated: int = 0
    skipped_duplicate: int = 0
    blocked: int = 0
    errors: int = 0
    dry_run: bool = False
    created_cards: list[dict[str, Any]] = field(default_factory=list)
    duplicates: list[dict[str, Any]] = field(default_factory=list)
    blocked_items: list[dict[str, Any]] = field(default_factory=list)
    error_items: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_type": self.source_type, "input_file": self.input_file,
            "started_at": self.started_at, "finished_at": self.finished_at,
            "total_seen": self.total_seen, "created": self.created, "updated": self.updated,
            "skipped_duplicate": self.skipped_duplicate, "blocked": self.blocked,
            "errors": self.errors, "dry_run": self.dry_run,
            "created_cards": self.created_cards, "duplicates": self.duplicates,
            "blocked_items": self.blocked_items, "error_items": self.error_items,
        }
