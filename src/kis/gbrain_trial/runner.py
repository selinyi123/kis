"""Trial run orchestration (KIS-016). Writes baseline/gbrain results as JSONL."""

from __future__ import annotations

import json
import os
from typing import Any

from . import baseline_search
from .adapters import GBrainAnswer


def _write_jsonl(path: str, rows: list[dict[str, Any]]) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        for r in rows:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")


def run_baseline(export_dir: str, questions: list[dict[str, Any]], run_dir: str,
                 limit: int | None = None) -> list[dict[str, Any]]:
    docs = baseline_search.load_docs(export_dir)
    qs = questions[:limit] if limit else questions
    rows = [{"question_id": q["id"], "question": q["question"],
             "results": baseline_search.search(q["question"], docs, top_k=3)} for q in qs]
    _write_jsonl(os.path.join(run_dir, "baseline_results.jsonl"), rows)
    return rows


def run_gbrain(adapter: Any, questions: list[dict[str, Any]], run_dir: str,
               export_dir: str, limit: int | None = None) -> list[dict[str, Any]]:
    adapter.index(export_dir)  # may raise AdapterUnavailable
    qs = questions[:limit] if limit else questions
    answers: list[GBrainAnswer] = [adapter.ask(q["id"], q["question"]) for q in qs]
    rows = [a.to_dict() for a in answers]
    _write_jsonl(os.path.join(run_dir, "gbrain_results.jsonl"), rows)
    return rows


def load_jsonl(path: str) -> list[dict[str, Any]]:
    if not os.path.exists(path):
        return []
    with open(path, encoding="utf-8") as fh:
        return [json.loads(line) for line in fh if line.strip()]
