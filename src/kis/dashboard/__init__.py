"""KIS-015 Review Dashboard — a read-only Obsidian view layer.

Renders static Markdown boards (overview / inbox / canonical candidates /
archive candidates / deferred / rejected / stats) from the card store.

HARD RULES:
  * View layer, NOT a source of truth — never writes the store, never changes
    lifecycle/review/source.
  * Generates *suggested* CLI commands only (copy-paste), never executes them.
  * Never emits an approve/canonical command on the Inbox page (canonical comes
    only from `reviewed` via the KIS-014 human gate).
  * Fully offline, deterministic, idempotent (output stable given a fixed
    generated_at).
"""

GENERATOR_VERSION = "kis-dashboard-0.3.2"

__all__ = ["GENERATOR_VERSION"]
