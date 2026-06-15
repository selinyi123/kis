"""GBrain adapters (KIS-016). GBrain is NEVER a hard dependency.

  * MockGBrainAdapter      — offline, deterministic (baseline-backed). Tests use this.
  * ManualGBrainAdapter    — replays a user-provided JSONL of GBrain answers.
  * SubprocessGBrainAdapter — calls a local gbrain CLI if present; fails cleanly.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from dataclasses import dataclass, field
from typing import Any

from . import baseline_search


class AdapterUnavailable(RuntimeError):
    """Raised when a real GBrain backend is not available."""


@dataclass
class GBrainAnswer:
    question_id: str
    question: str
    answer: str
    citations: list[dict[str, Any]] = field(default_factory=list)
    gaps: list[str] = field(default_factory=list)
    conflicts: list[str] = field(default_factory=list)
    stale_warnings: list[str] = field(default_factory=list)
    entities: list[str] = field(default_factory=list)
    relations: list[dict[str, Any]] = field(default_factory=list)
    raw: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "question_id": self.question_id, "question": self.question, "answer": self.answer,
            "citations": self.citations, "gaps": self.gaps, "conflicts": self.conflicts,
            "stale_warnings": self.stale_warnings, "entities": self.entities,
            "relations": self.relations, "raw": self.raw,
        }


_KNOWN_ENTITIES = ("ClipVault", "Obsidian", "DPMS", "Prompt Performance Engine", "KIS",
                   "GBrain", "MemOS", "Crawl4AI", "MediaCrawler", "Agent-Reach", "GitHub Stars")


class MockGBrainAdapter:
    """Deterministic, offline. Answers from baseline; citations are real export paths."""
    name = "mock"

    def __init__(self, export_dir: str):
        self.export_dir = export_dir
        self._docs: list[tuple[str, str]] = []

    def index(self, export_dir: str | None = None) -> None:
        self._docs = baseline_search.load_docs(export_dir or self.export_dir)

    def ask(self, question_id: str, question: str) -> GBrainAnswer:
        hits = baseline_search.search(question, self._docs, top_k=3)
        entities = [e for e in _KNOWN_ENTITIES if e.lower() in question.lower()]
        if not hits:
            return GBrainAnswer(question_id, question, "unknown — no source found in export",
                                gaps=["no matching source in exported snapshot"], entities=entities)
        cites = [{"path": h["path"], "quote_or_snippet": h["snippet"],
                  "line_start": None, "line_end": None} for h in hits]
        answer = f"Based on {len(hits)} source(s): {hits[0]['snippet']}"
        relations = []
        if "ClipVault" in entities and "Obsidian" in entities:
            relations = [{"source": "ClipVault", "relation": "writes_to", "target": "Obsidian",
                          "evidence_path": hits[0]["path"]}]
        return GBrainAnswer(question_id, question, answer, citations=cites,
                            entities=entities, relations=relations, raw={"backend": "mock"})


class ManualGBrainAdapter:
    """Replays answers a human produced with a real GBrain, stored as JSONL."""
    name = "manual"

    def __init__(self, results_path: str):
        self.results_path = results_path
        self._by_id: dict[str, dict[str, Any]] = {}

    def index(self, export_dir: str | None = None) -> None:
        if not os.path.exists(self.results_path):
            raise AdapterUnavailable(f"manual results file not found: {self.results_path}")
        with open(self.results_path, encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if line:
                    rec = json.loads(line)
                    self._by_id[rec["question_id"]] = rec

    def ask(self, question_id: str, question: str) -> GBrainAnswer:
        rec = self._by_id.get(question_id)
        if not rec:
            return GBrainAnswer(question_id, question, "unknown — no manual answer provided",
                                gaps=["manual answer missing"])
        return GBrainAnswer(
            question_id, question, rec.get("answer", ""), citations=rec.get("citations", []),
            gaps=rec.get("gaps", []), conflicts=rec.get("conflicts", []),
            stale_warnings=rec.get("stale_warnings", []), entities=rec.get("entities", []),
            relations=rec.get("relations", []), raw={"backend": "manual"})


import re as _re

# GBrain `query`/`search` CLI line: "[0.8748] some/slug -- snippet text"
_GBRAIN_LINE = _re.compile(r"^\[(?P<score>\d*\.?\d+)\]\s+(?P<slug>\S+)\s+--\s+(?P<snip>.*)$")


def parse_gbrain_query_output(text: str) -> list[dict[str, Any]]:
    """Parse real `gbrain query` text output into citation dicts (path=slug)."""
    cites: list[dict[str, Any]] = []
    for line in (text or "").splitlines():
        m = _GBRAIN_LINE.match(line.strip())
        if m:
            cites.append({"path": m.group("slug"), "quote_or_snippet": m.group("snip").strip(),
                          "line_start": None, "line_end": None, "score": float(m.group("score"))})
    return cites


class SubprocessGBrainAdapter:
    """Calls the real gbrain CLI. Brain is prepared out-of-band (init + import);
    this adapter only queries. Uses `gbrain query <q> --limit N` and parses the
    `[score] slug -- snippet` output into citations. Never used by mock tests."""
    name = "subprocess"

    def __init__(self, export_dir: str, binary: str = "gbrain", limit: int = 8, query_cmd: str = "query"):
        self.export_dir = export_dir
        self.binary = binary
        self.limit = limit
        self.query_cmd = query_cmd

    def _resolve(self) -> str:
        if os.path.isfile(self.binary):
            return self.binary
        found = shutil.which(self.binary)
        if found:
            return found
        raise AdapterUnavailable(f"gbrain CLI not found: {self.binary}")

    def index(self, export_dir: str | None = None) -> None:
        self._resolve()  # verify availability; brain built out-of-band (init+import)

    def ask(self, question_id: str, question: str) -> GBrainAnswer:
        exe = self._resolve()
        out = subprocess.run([exe, self.query_cmd, question, "--limit", str(self.limit)],
                             capture_output=True, text=True, encoding="utf-8")
        cites = parse_gbrain_query_output(out.stdout)
        answer = (f"Top {len(cites)} GBrain hit(s): {cites[0]['quote_or_snippet']}"
                  if cites else "unknown — gbrain returned no result")
        entities = [e for e in _KNOWN_ENTITIES if e.lower() in question.lower()]
        return GBrainAnswer(question_id, question, answer, citations=cites, entities=entities,
                            raw={"backend": "subprocess", "stdout": (out.stdout or "")[:2000],
                                 "stderr": (out.stderr or "")[:500]})
