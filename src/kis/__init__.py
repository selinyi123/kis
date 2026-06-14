"""KIS — Knowledge Intelligence System.

v0.1 minimal runnable closed loop:
    source connector -> KnowledgeCard -> validate -> SQLite store -> Obsidian export

Zero third-party runtime dependencies (pure stdlib), following the ClipVault
desktop discipline. The schema is the contract (PPE discipline): unknown fields
are rejected, scoring/cleaning are deterministic, LLM enrichment is deferred to
v0.2.
"""

SCHEMA_VERSION = "0.1.0"

__all__ = ["SCHEMA_VERSION"]
