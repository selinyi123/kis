"""Render the trial report (KIS-016). Read-only output; never a source of truth."""

from __future__ import annotations

from typing import Any

from .manifest import now_iso


def decide(metrics: dict[str, Any]) -> dict[str, str]:
    safe = (
        metrics.get("citation_traceability", 0) >= 0.95
        and metrics.get("sensitive_leakage_count", 1) == 0
        and metrics.get("wrong_relation_count", 99) <= 1
        and metrics.get("missing_source_rate", 1.0) <= 0.10
    )
    # A requires a real gain over the free keyword baseline: meaningfully higher
    # usefulness AND not just returning the same docs (low overlap). Otherwise B.
    differentiates = metrics.get("baseline_overlap", 1.0) < 0.6
    useful_gain = metrics.get("answer_usefulness_score", 0) > metrics.get("baseline_usefulness_score", 0) + 0.05
    promote = safe and differentiates and useful_gain
    return {
        "promote_to_kis017": "yes" if promote else "no",
        "keep_readonly": "yes",
        "allow_writeback": "no",
        "allow_canonical": "no",
        "verdict": "A" if promote else ("C" if not safe else "B"),
    }


def render_report(manifest: dict[str, Any], questions: list[dict[str, Any]],
                  evaluation: dict[str, Any], adapter_name: str,
                  gbrain_executed: bool, failures: list[str]) -> str:
    m = evaluation["metrics"]
    d = decide(m)
    summary = manifest.get("summary", {})
    lines = [
        "# KIS-016 GBrain Read-Only Trial Report", "",
        f"_generated_at: {now_iso()} · adapter: {adapter_name} · real_gbrain_executed: {gbrain_executed}_", "",
        "## Summary", "",
        "| Metric | Value |", "|---|---:|",
        f"| Questions | {len(questions)} |",
        f"| Exported files | {summary.get('included_count', 0)} |",
        f"| Denied files | {summary.get('denied_count', 0)} |",
        f"| Citation traceability | {m['citation_traceability']} |",
        f"| Missing-source rate | {m['missing_source_rate']} |",
        f"| Unknown-when-no-source rate | {m['unknown_when_no_source_rate']} |",
        f"| Sensitive leakage count | {m['sensitive_leakage_count']} |",
        f"| Wrong relation count | {m['wrong_relation_count']} |",
        f"| Conflicts flagged | {m['conflict_detection_count']} |",
        f"| Stale warnings | {m['stale_warning_count']} |",
        f"| Baseline overlap | {m['baseline_overlap']} |",
        f"| Answer usefulness — GBrain | {m['answer_usefulness_score']} |",
        f"| Answer usefulness — keyword baseline | {m.get('baseline_usefulness_score', 'n/a')} |",
        "",
        "## Export Scope", "",
        f"- Source vault: `{manifest.get('source_vault', '')}`",
        f"- Included: {summary.get('included_count', 0)} files, {summary.get('total_bytes', 0)} bytes",
        "",
        "## Denied Files", "",
    ]
    denied = manifest.get("denied_files", [])
    if denied:
        lines += ["| Path | Reason |", "|---|---|"]
        lines += [f"| {f['source_path']} | {f['reason']} |" for f in denied[:50]]
    else:
        lines.append("_(none)_")

    lines += ["", "## Questions", "", f"{len(questions)} trial questions (see questions.jsonl).", ""]
    lines += ["## Baseline vs GBrain", "",
              "Baseline = offline keyword/FTS search; GBrain = derived index under test.",
              "Per-question scores in evaluation.json.", ""]
    lines += ["## Citation Traceability", "",
              f"{m['citation_traceability']} of answers cite only files present in the export.", ""]
    lines += ["## Gaps / Conflicts / Stale Data", "",
              f"- conflicts flagged: {m['conflict_detection_count']}",
              f"- stale warnings: {m['stale_warning_count']}", ""]
    lines += ["## Entity Relation Audit", ""]
    ra = evaluation.get("relation_audit", [])
    lines.append(f"- unsupported relations: {m['wrong_relation_count']}" + ("" if ra else " (none)"))
    lines += ["", "## Sensitive Leakage Audit", ""]
    la = evaluation.get("leakage_audit", [])
    lines.append(f"- leakage incidents: {m['sensitive_leakage_count']}" + ("" if la else " (none)"))
    lines += ["", "## Failures", ""]
    lines += ([f"- {f}" for f in failures] if failures else ["_(none)_"])
    lines += ["", "## Decision", "",
              f"- verdict: {d.get('verdict', '?')}",
              f"- promote_to_kis017: {d['promote_to_kis017']}",
              f"- keep_readonly: {d['keep_readonly']}",
              f"- allow_writeback: {d['allow_writeback']}",
              f"- allow_canonical: {d['allow_canonical']}", ""]
    return "\n".join(lines)
