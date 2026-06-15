"""Secret guard for external ingestion (KIS-018).

Items whose text carries a credential shape are BLOCKED: never stored, never
written to Obsidian — only recorded in the report.
"""

from __future__ import annotations

import re

# Credential shapes + assignment-style secrets. '=' suffixes avoid flagging
# benign words ("session management") while catching "token=...".
_PATTERNS: list[tuple[str, re.Pattern]] = [
    ("openai_key", re.compile(r"sk-[A-Za-z0-9]{16,}")),
    ("github_token", re.compile(r"ghp_[A-Za-z0-9]{20,}")),
    ("aws_key", re.compile(r"AKIA[0-9A-Z]{12,}")),
    ("private_key", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")),
    ("password_assign", re.compile(r"password\s*=", re.I)),
    ("token_assign", re.compile(r"token\s*=", re.I)),
    ("cookie_assign", re.compile(r"cookie\s*=", re.I)),
    ("session_assign", re.compile(r"session\s*=", re.I)),
    ("otp", re.compile(r"\botp\b", re.I)),
    ("dotenv", re.compile(r"\.env\b", re.I)),
]


def scan_secrets(*texts: str) -> list[str]:
    """Return the names of secret patterns found across the given texts."""
    blob = "\n".join(t for t in texts if t)
    return [name for name, pat in _PATTERNS if pat.search(blob)]


def is_blocked(*texts: str) -> tuple[bool, str | None]:
    hits = scan_secrets(*texts)
    return (bool(hits), ("secret:" + ",".join(hits)) if hits else None)
