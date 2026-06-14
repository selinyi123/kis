"""SQLite + FTS5 store with idempotent upsert and an append-only event log.

Design mirrors ClipVault (content_hash idempotency, event outbox as the source
of truth) and DPMS (insert_if_new). Re-running ingest never duplicates a card:
the deterministic ``id`` is the primary key; ``content_hash`` decides whether an
existing card is "unchanged" or "updated".
"""

from __future__ import annotations

import json
import sqlite3
from typing import Any

from .card import now_iso

_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS cards (
    id            TEXT PRIMARY KEY,
    content_hash  TEXT NOT NULL,
    connector     TEXT NOT NULL,
    url           TEXT NOT NULL,
    title         TEXT NOT NULL,
    body_md       TEXT NOT NULL,
    summary       TEXT,
    category      TEXT,
    tags_json     TEXT,
    projects_json TEXT,
    value_score   INTEGER,
    value_level   TEXT,
    evidence_level TEXT,
    state         TEXT,
    created_at    TEXT,
    updated_at    TEXT,
    version       INTEGER,
    card_json     TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_cards_connector ON cards(connector);
CREATE INDEX IF NOT EXISTS idx_cards_state ON cards(state);

CREATE TABLE IF NOT EXISTS events (
    seq        INTEGER PRIMARY KEY AUTOINCREMENT,
    ts         TEXT NOT NULL,
    card_id    TEXT NOT NULL,
    event_type TEXT NOT NULL,
    payload    TEXT
);
"""

_FTS_SQL = """
CREATE VIRTUAL TABLE IF NOT EXISTS cards_fts
USING fts5(id UNINDEXED, title, body, summary, tags);
"""


class Store:
    def __init__(self, path: str = "kis.db"):
        self.path = path
        self.conn = sqlite3.connect(path)
        self.conn.row_factory = sqlite3.Row
        self.fts_enabled = False
        self._init_db()

    def _init_db(self) -> None:
        self.conn.executescript(_SCHEMA_SQL)
        try:
            self.conn.executescript(_FTS_SQL)
            self.fts_enabled = True
        except sqlite3.OperationalError:
            # FTS5 not compiled into this sqlite build — search degrades to LIKE.
            self.fts_enabled = False
        self.conn.commit()

    def close(self) -> None:
        self.conn.close()

    # -- write path -----------------------------------------------------------

    def upsert(self, card: dict[str, Any]) -> str:
        """Insert or update a card. Returns 'inserted' | 'updated' | 'unchanged'."""
        cid = card["id"]
        row = self.conn.execute(
            "SELECT content_hash, version FROM cards WHERE id = ?", (cid,)
        ).fetchone()

        if row is None:
            status = "inserted"
            version = 1
        elif row["content_hash"] == card["content_hash"]:
            self._log_event(cid, "unchanged", {"content_hash": card["content_hash"]})
            return "unchanged"
        else:
            status = "updated"
            version = int(row["version"]) + 1
            card["lifecycle"]["version"] = version
            card["lifecycle"]["updated_at"] = now_iso()

        enr = card["enrichment"]
        life = card["lifecycle"]
        self.conn.execute(
            """INSERT INTO cards (id, content_hash, connector, url, title, body_md,
                   summary, category, tags_json, projects_json, value_score,
                   value_level, evidence_level, state, created_at, updated_at,
                   version, card_json)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
               ON CONFLICT(id) DO UPDATE SET
                   content_hash=excluded.content_hash,
                   title=excluded.title, body_md=excluded.body_md,
                   summary=excluded.summary, category=excluded.category,
                   tags_json=excluded.tags_json, projects_json=excluded.projects_json,
                   value_score=excluded.value_score, value_level=excluded.value_level,
                   evidence_level=excluded.evidence_level, state=excluded.state,
                   updated_at=excluded.updated_at, version=excluded.version,
                   card_json=excluded.card_json""",
            (
                cid, card["content_hash"], card["source"]["connector"], card["source"]["url"],
                card["content"]["title"], card["content"]["body_md"],
                enr.get("summary", ""), enr.get("category", ""),
                json.dumps(enr.get("tags", []), ensure_ascii=False),
                json.dumps(card["linkage"].get("projects", []), ensure_ascii=False),
                enr.get("value_score", 0), enr.get("value_level", "cold"),
                enr.get("evidence_level", "heuristic"), life.get("state", "inbox"),
                life.get("created_at"), life.get("updated_at"), version,
                json.dumps(card, ensure_ascii=False),
            ),
        )
        self._sync_fts(card)
        self._log_event(cid, status, {"content_hash": card["content_hash"], "version": version})
        self.conn.commit()
        return status

    def _sync_fts(self, card: dict[str, Any]) -> None:
        if not self.fts_enabled:
            return
        cid = card["id"]
        self.conn.execute("DELETE FROM cards_fts WHERE id = ?", (cid,))
        self.conn.execute(
            "INSERT INTO cards_fts (id, title, body, summary, tags) VALUES (?,?,?,?,?)",
            (
                cid, card["content"]["title"], card["content"]["body_md"],
                card["enrichment"].get("summary", ""),
                " ".join(card["enrichment"].get("tags", [])),
            ),
        )

    def _log_event(self, card_id: str, event_type: str, payload: dict[str, Any]) -> None:
        self.conn.execute(
            "INSERT INTO events (ts, card_id, event_type, payload) VALUES (?,?,?,?)",
            (now_iso(), card_id, event_type, json.dumps(payload, ensure_ascii=False)),
        )

    # -- read path ------------------------------------------------------------

    def count(self) -> int:
        return self.conn.execute("SELECT COUNT(*) AS n FROM cards").fetchone()["n"]

    def get(self, card_id: str) -> dict[str, Any] | None:
        row = self.conn.execute("SELECT card_json FROM cards WHERE id = ?", (card_id,)).fetchone()
        return json.loads(row["card_json"]) if row else None

    def all_cards(self) -> list[dict[str, Any]]:
        rows = self.conn.execute("SELECT card_json FROM cards ORDER BY created_at").fetchall()
        return [json.loads(r["card_json"]) for r in rows]

    def search(self, query: str, limit: int = 20) -> list[dict[str, Any]]:
        if self.fts_enabled:
            rows = self.conn.execute(
                """SELECT c.card_json FROM cards_fts f JOIN cards c ON c.id = f.id
                   WHERE cards_fts MATCH ? LIMIT ?""",
                (query, limit),
            ).fetchall()
        else:
            like = f"%{query}%"
            rows = self.conn.execute(
                """SELECT card_json FROM cards
                   WHERE title LIKE ? OR body_md LIKE ? OR summary LIKE ? LIMIT ?""",
                (like, like, like, limit),
            ).fetchall()
        return [json.loads(r["card_json"]) for r in rows]
