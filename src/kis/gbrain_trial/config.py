"""Trial configuration: output paths, allowlist, deny policy (KIS-016)."""

from __future__ import annotations

DEFAULT_OUT_DIR = ".kis/gbrain_trial"
DEFAULT_VAULT = r"D:\TOOL\OBSIDIAN\Home\prompt仓库\KIS 知识情报系统"

# Only files whose top-level directory is here (or root-level files) may export.
ALLOWLIST_DIRS = {
    "Dashboards", "GitHub-Stars", "Browser-Bookmarks", "Web-Clips",
    "ClipVault Personal", "Prompt Performance Engine", "DPMS-Platform",
}

# Conservative deny tokens — matched as substrings of the lowercased path. A
# trial favours EXCLUSION: a falsely-excluded card is harmless; a leaked
# credential is not.
DENY_TOKENS = (
    "blocked", "secret", "confidential", "private", "token", "cookie", "credential",
    "profile", "qr", "session", "proxy", "password", "otp", "auth", "key", ".env",
)

DENY_EXTENSIONS = (".db", ".sqlite", ".sqlite3", ".env", ".key", ".pem", ".p12", ".pfx",
                   ".jsonl", ".exe", ".dll", ".bin", ".zip", ".png", ".jpg", ".jpeg", ".gif", ".pdf")
ALLOW_EXTENSIONS = (".md", ".txt")  # .json only if explicitly allowlisted
JSON_ALLOWLIST: frozenset[str] = frozenset()  # none by default

MAX_FILE_BYTES = 1_000_000  # >1MB treated as a raw export -> denied

INTERNAL_HINTS = ("ops-internal", "internal", "trading-research")
