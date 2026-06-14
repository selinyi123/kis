"""KIS — Knowledge Intelligence System.

v0.2a multi-source closed loop:
    source connector -> KnowledgeCard -> validate -> SQLite store -> Obsidian export

Connectors: GitHub Stars (v0.1), Browser Bookmarks (v0.2a).

Zero third-party runtime dependencies (pure stdlib), following the ClipVault
desktop discipline. The schema is the contract (PPE discipline): unknown fields
are rejected, scoring/cleaning are deterministic, LLM enrichment is deferred to
v0.3. Source-imported cards carry authority="source" and evidence_level="source"
— they are raw provenance, never derived claims.
"""

SCHEMA_VERSION = "0.2.0"

__all__ = ["SCHEMA_VERSION"]
