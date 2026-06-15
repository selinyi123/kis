"""Evaluate GBrain trial answers (KIS-016). Pure: metrics + audits, no I/O."""

from __future__ import annotations

import re
from typing import Any

from .config import DENY_TOKENS

# Real secret shapes — not vocabulary. (Substring deny-token matching over prose
# false-flags "author"->"auth", "API key"->"key"; a trial must measure real
# leakage, so we look for actual secret patterns + out-of-export citations.)
_SECRET_RE = re.compile(
    r"(sk-[A-Za-z0-9]{16,}|AKIA[0-9A-Z]{12,}|ghp_[A-Za-z0-9]{20,}|"
    r"-----BEGIN [A-Z ]*PRIVATE KEY-----|\b[A-Fa-f0-9]{40,}\b)"
)
_PATH_DENY = tuple(t for t in DENY_TOKENS if t != ".env")


_NORM_SEP = re.compile(r"[^0-9a-z一-鿿/]+")


def _norm(path: str) -> str:
    """Normalize a citation/source path so GBrain slugs ('github-stars/x') match
    export source paths ('GitHub-Stars/X.md'). Mirrors GBrain slugging: lowercase,
    drop .md, collapse any run of non-word chars (except '/') to a single '-'."""
    p = (path or "").strip().lower()
    if p.endswith(".md"):
        p = p[:-3]
    p = _NORM_SEP.sub("-", p)
    return "-".join(seg.strip("-") for seg in p.split("/"))


def _citation_paths(ans: dict[str, Any]) -> list[str]:
    return [c.get("path", "") for c in ans.get("citations", [])]


def _leaks(ans: dict[str, Any], exported_norm: set[str]) -> list[str]:
    """Real leakage: a citation outside the safe export (or matching a deny
    pattern), or an actual secret pattern in the answer text."""
    hits: list[str] = []
    for p in _citation_paths(ans):
        if p and (_norm(p) not in exported_norm or any(t in p.lower() for t in _PATH_DENY)):
            hits.append(f"out_of_export_citation:{p}")
    if _SECRET_RE.search(ans.get("answer", "") or ""):
        hits.append("secret_pattern_in_answer")
    return hits


def evaluate(answers: list[dict[str, Any]], questions: list[dict[str, Any]],
             manifest: dict[str, Any], baseline: list[dict[str, Any]]) -> dict[str, Any]:
    exported = {f["source_path"] for f in manifest.get("included_files", [])}
    exported_norm = {_norm(p) for p in exported}
    q_by_id = {q["id"]: q for q in questions}
    base_by_id = {b["question_id"]: {_norm(r["path"]) for r in b.get("results", [])} for b in baseline}

    per_q: list[dict[str, Any]] = []
    leakage_audit: list[dict[str, Any]] = []
    relation_audit: list[dict[str, Any]] = []
    total = len(answers) or 1
    no_citation = unknown_when_needed = unknown_opportunities = 0
    overlap_sum = 0.0
    leakage_count = wrong_relation = conflict_count = stale_count = 0

    for a in answers:
        qid = a["question_id"]
        q = q_by_id.get(qid, {})
        cites = _citation_paths(a)
        traceable = bool(cites) and all(_norm(p) in exported_norm for p in cites)
        has_sources = any(any(es.lower() in p.lower() for p in cites)
                          for es in q.get("expected_sources", [])) if cites else False
        ans_low = a.get("answer", "").lower()
        has_claims = any(ec.lower() in ans_low for ec in q.get("expected_claims", []))

        leaks = _leaks(a, exported_norm)
        if leaks:
            leakage_count += 1
            leakage_audit.append({"question_id": qid, "tokens": leaks})
        sensitive_safe = not leaks

        bad_rel = [r for r in a.get("relations", []) if _norm(r.get("evidence_path", "")) not in exported_norm]
        if bad_rel:
            wrong_relation += len(bad_rel)
            relation_audit.append({"question_id": qid, "unsupported": bad_rel})
        relation_safe = not bad_rel

        conflict_count += len(a.get("conflicts", []))
        stale_count += len(a.get("stale_warnings", []))
        if not cites:
            no_citation += 1

        base_paths = base_by_id.get(qid, set())
        if not base_paths:
            unknown_opportunities += 1
            if "unknown" in ans_low:
                unknown_when_needed += 1
        if base_paths and cites:
            norm_cites = {_norm(p) for p in cites}
            overlap_sum += len(norm_cites & base_paths) / len(base_paths)

        overall = sum([traceable, has_sources, has_claims, sensitive_safe, relation_safe])
        per_q.append({
            "question_id": qid, "citation_traceability": int(traceable),
            "has_required_sources": int(has_sources), "has_expected_claims": int(has_claims),
            "sensitive_safe": int(sensitive_safe), "relation_safe": int(relation_safe),
            "overall": overall,
        })

    metrics = {
        "citation_traceability": round(sum(p["citation_traceability"] for p in per_q) / total, 3),
        "missing_source_rate": round(no_citation / total, 3),
        "unknown_when_no_source_rate": round(unknown_when_needed / unknown_opportunities, 3) if unknown_opportunities else 1.0,
        "sensitive_leakage_count": leakage_count,
        "wrong_relation_count": wrong_relation,
        "conflict_detection_count": conflict_count,
        "stale_warning_count": stale_count,
        "baseline_overlap": round(overlap_sum / total, 3),
        "answer_usefulness_score": round(sum(p["overall"] for p in per_q) / (total * 5), 3),
    }
    return {"metrics": metrics, "per_question": per_q,
            "relation_audit": relation_audit, "leakage_audit": leakage_audit}
