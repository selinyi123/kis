"""Safe-export filter (KIS-016). Pure: decides if a vault file may be exported."""

from __future__ import annotations

import os
from dataclasses import dataclass

from .config import (
    ALLOW_EXTENSIONS, ALLOWLIST_DIRS, DENY_EXTENSIONS, DENY_TOKENS, INTERNAL_HINTS,
    JSON_ALLOWLIST, MAX_FILE_BYTES,
)


@dataclass
class FilterResult:
    allowed: bool
    reason: str
    sensitivity: str = "public"


def _looks_binary(data: bytes) -> bool:
    # NUL byte is the canonical binary signal. We deliberately do NOT strict-
    # decode the 4 KB head: a head can split a multibyte UTF-8 char and raise a
    # false error (real binaries are already caught by DENY_EXTENSIONS + NUL).
    return b"\x00" in data


def classify_file(rel_path: str, size_bytes: int, head_bytes: bytes = b"") -> FilterResult:
    """Decide export eligibility for one file. rel_path is vault-relative (use '/')."""
    rp = rel_path.replace("\\", "/")
    low = rp.lower()
    ext = os.path.splitext(low)[1]

    if ext in DENY_EXTENSIONS:
        return FilterResult(False, f"deny extension: {ext}")
    for tok in DENY_TOKENS:
        if tok in low:
            return FilterResult(False, f"deny pattern: {tok}")
    if ext == ".json":
        if rp not in JSON_ALLOWLIST:
            return FilterResult(False, "json not allowlisted")
    elif ext not in ALLOW_EXTENSIONS:
        return FilterResult(False, f"ext not allowed: {ext or '(none)'}")

    top = rp.split("/")[0] if "/" in rp else ""
    if top and top not in ALLOWLIST_DIRS:
        return FilterResult(False, f"dir not allowlisted: {top}")

    if size_bytes > MAX_FILE_BYTES:
        return FilterResult(False, f"too large: {size_bytes} bytes")
    if head_bytes and _looks_binary(head_bytes):
        return FilterResult(False, "binary content")

    sensitivity = "internal" if any(h in low for h in INTERNAL_HINTS) else "public"
    reason = "allowlisted directory" if top else "allowlisted root note"
    return FilterResult(True, reason, sensitivity)
