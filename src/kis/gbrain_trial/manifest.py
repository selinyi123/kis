"""Export manifest + content hashing (KIS-016)."""

from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from typing import Any

from . import TRIAL_VERSION


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def content_hash(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()[:16]


def build_manifest(source_vault: str, export_dir: str, included: list[dict[str, Any]],
                   denied: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "generated_at": now_iso(),
        "kis_version": TRIAL_VERSION,
        "source_vault": source_vault,
        "export_dir": export_dir,
        "included_files": included,
        "denied_files": denied,
        "summary": {
            "included_count": len(included),
            "denied_count": len(denied),
            "total_bytes": sum(f.get("size_bytes", 0) for f in included),
        },
    }
