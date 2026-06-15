"""KIS-018 External Inbox Ingestion.

Safe, auditable, reproducible ingestion of EXTERNAL material into the inbox:

    external source -> adapter -> safety + normalize + dedupe -> store(inbox)
        -> Obsidian External-Inbox -> review queue (KIS-014)

Hard rules:
  * Everything lands in lifecycle.state = inbox — never auto reviewed/canonical.
  * Secret-bearing items (API keys, tokens, private keys, .env) are BLOCKED:
    not stored, not written to Obsidian, only logged in the report.
  * No network fetch (KIS-018 ingests already-exported files); no login-walled or
    private data; never overwrites an existing canonical/reviewed card.
  * Dedupe on normalized_url / content_hash / (source_type, source_id).
  * dry-run previews with the same counts as a real run.
"""

# CLI source name -> schema source_type (reuse existing enum; browser_bookmark == web_bookmark)
SOURCE_TYPE = {
    "github-stars": "github_star",
    "bookmarks": "web_bookmark",
    "web-clips": "web_clip",
}
INBOX_FOLDER = {
    "github_star": "GitHub-Stars",
    "web_bookmark": "Browser-Bookmarks",
    "web_clip": "Web-Clips",
}

__all__ = ["SOURCE_TYPE", "INBOX_FOLDER"]
