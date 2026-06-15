"""KIS-016 GBrain read-only trial CLI.

Pipeline: export (safe snapshot) -> questions -> baseline -> run (adapter) ->
evaluate -> report. GBrain is never a hard dependency; mock/manual run offline,
subprocess is optional and degrades to baseline+report on failure.

Usage (PowerShell):
    python scripts/gbrain_trial.py export --dry-run
    python scripts/gbrain_trial.py export --vault-dir "...\\KIS 知识情报系统"
    python scripts/gbrain_trial.py questions
    python scripts/gbrain_trial.py baseline
    python scripts/gbrain_trial.py run --adapter mock
    python scripts/gbrain_trial.py evaluate
    python scripts/gbrain_trial.py report
    python scripts/gbrain_trial.py all --adapter mock
"""

from __future__ import annotations

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

from kis.gbrain_trial import evaluator, report, runner  # noqa: E402
from kis.gbrain_trial.adapters import (  # noqa: E402
    AdapterUnavailable, ManualGBrainAdapter, MockGBrainAdapter, SubprocessGBrainAdapter,
)
from kis.gbrain_trial.config import DEFAULT_OUT_DIR, DEFAULT_VAULT  # noqa: E402
from kis.gbrain_trial.exporter import export_vault  # noqa: E402
from kis.gbrain_trial.questions import QUESTIONS, write_questions  # noqa: E402


def _paths(out_dir: str):
    return (os.path.join(out_dir, "exported_vault"),
            os.path.join(out_dir, "manifests", "export_manifest.json"),
            os.path.join(out_dir, "runs", "latest"))


def _load_questions(path: str | None):
    if not path:
        return QUESTIONS
    return runner.load_jsonl(path)


def _load_manifest(mpath: str):
    if not os.path.exists(mpath):
        return {"included_files": [], "denied_files": [], "summary": {}}
    with open(mpath, encoding="utf-8") as fh:
        return json.load(fh)


def _build_adapter(name: str, export_dir: str, run_dir: str, gbrain_binary: str = "gbrain"):
    if name == "mock":
        return MockGBrainAdapter(export_dir)
    if name == "manual":
        return ManualGBrainAdapter(os.path.join(run_dir, "gbrain_manual_input.jsonl"))
    if name == "subprocess":
        return SubprocessGBrainAdapter(export_dir, binary=gbrain_binary)
    raise SystemExit(f"unknown adapter: {name}")


def cmd_export(args):
    m = export_vault(args.vault_dir, args.out_dir, dry_run=args.dry_run)
    s = m["summary"]
    tag = "DRY-RUN " if args.dry_run else ""
    print(f"[kis] {tag}export: included={s['included_count']} denied={s['denied_count']} bytes={s['total_bytes']}")
    return 0


def cmd_questions(args):
    if args.dry_run:
        print(f"[kis] DRY-RUN questions: {len(QUESTIONS)} (not written)"); return 0
    print(f"[kis] wrote {len(QUESTIONS)} questions -> {write_questions(args.out_dir)}"); return 0


def cmd_baseline(args):
    export_dir, _, run_dir = _paths(args.out_dir)
    rows = runner.run_baseline(export_dir, _load_questions(args.questions), run_dir, args.limit)
    print(f"[kis] baseline: {len(rows)} questions searched -> {run_dir}/baseline_results.jsonl")
    return 0


def cmd_manual_template(args):
    """Emit a stub JSONL (20 questions) for a human to fill from a real GBrain
    session, then `run --adapter manual` consumes it. Turnkey manual path."""
    _, _, run_dir = _paths(args.out_dir)
    os.makedirs(run_dir, exist_ok=True)
    path = os.path.join(run_dir, "gbrain_manual_input.jsonl")
    if os.path.exists(path) and not args.force:
        print(f"[kis] manual template already exists (use --force to overwrite): {path}")
        return 0
    with open(path, "w", encoding="utf-8") as fh:
        for q in _load_questions(args.questions):
            fh.write(json.dumps({
                "question_id": q["id"], "question": q["question"], "answer": "",
                "citations": [], "gaps": [], "conflicts": [], "stale_warnings": [],
                "entities": [], "relations": [],
            }, ensure_ascii=False) + "\n")
    print(f"[kis] manual template -> {path}\n"
          f"      fill 'answer'/'citations' from a real GBrain session, then:\n"
          f"      python scripts/gbrain_trial.py run --adapter manual && ... evaluate && ... report")
    return 0


def cmd_run(args):
    export_dir, _, run_dir = _paths(args.out_dir)
    adapter = _build_adapter(args.adapter, export_dir, run_dir, getattr(args, "gbrain_binary", "gbrain"))
    try:
        rows = runner.run_gbrain(adapter, _load_questions(args.questions), run_dir, export_dir, args.limit)
        print(f"[kis] gbrain({args.adapter}): {len(rows)} answers -> {run_dir}/gbrain_results.jsonl")
        return 0
    except AdapterUnavailable as e:
        print(f"[kis] gbrain unavailable ({e}) — degraded to baseline/report only")
        return 0 if args.no_gbrain or args.adapter != "subprocess" else 1


def cmd_evaluate(args):
    export_dir, mpath, run_dir = _paths(args.out_dir)
    manifest = _load_manifest(mpath)
    answers = runner.load_jsonl(os.path.join(run_dir, "gbrain_results.jsonl"))
    baseline = runner.load_jsonl(os.path.join(run_dir, "baseline_results.jsonl"))
    questions = _load_questions(args.questions)
    ev = evaluator.evaluate(answers, questions, manifest, baseline)
    # Fair comparison: score the keyword baseline as if it were answers, so the
    # A/B/C verdict can require a real gain over the free baseline.
    base_answers = [{"question_id": b["question_id"], "question": b["question"],
                     "answer": (b.get("results") or [{}])[0].get("snippet", "unknown — no source"),
                     "citations": [{"path": r["path"]} for r in b.get("results", [])]}
                    for b in baseline]
    base_ev = evaluator.evaluate(base_answers, questions, manifest, baseline)
    ev["metrics"]["baseline_usefulness_score"] = base_ev["metrics"]["answer_usefulness_score"]
    ev["metrics"]["baseline_traceability"] = base_ev["metrics"]["citation_traceability"]
    os.makedirs(run_dir, exist_ok=True)
    for fn, obj in (("evaluation.json", ev), ("relation_audit.json", ev["relation_audit"]),
                    ("leakage_audit.json", ev["leakage_audit"])):
        with open(os.path.join(run_dir, fn), "w", encoding="utf-8") as fh:
            json.dump(obj, fh, ensure_ascii=False, indent=2)
    print(f"[kis] evaluate: {ev['metrics']}")
    if args.fail_on_leakage and ev["metrics"]["sensitive_leakage_count"] > 0:
        print("[kis] FAIL: sensitive leakage detected"); return 1
    return 0


def cmd_report(args):
    export_dir, mpath, run_dir = _paths(args.out_dir)
    manifest = _load_manifest(mpath)
    evp = os.path.join(run_dir, "evaluation.json")
    evaluation = json.load(open(evp, encoding="utf-8")) if os.path.exists(evp) else {
        "metrics": {k: 0 for k in ("citation_traceability", "missing_source_rate",
                    "unknown_when_no_source_rate", "sensitive_leakage_count", "wrong_relation_count",
                    "conflict_detection_count", "stale_warning_count", "baseline_overlap",
                    "answer_usefulness_score")}, "relation_audit": [], "leakage_audit": []}
    md = report.render_report(manifest, _load_questions(args.questions), evaluation,
                              args.adapter, gbrain_executed=(args.adapter == "subprocess"), failures=[])
    os.makedirs(run_dir, exist_ok=True)
    out = os.path.join(run_dir, "trial_report.md")
    with open(out, "w", encoding="utf-8") as fh:
        fh.write(md)
    print(f"[kis] report -> {out}")
    print(f"      decision: {report.decide(evaluation['metrics'])}")
    return 0


def cmd_all(args):
    for fn in (cmd_export, cmd_questions, cmd_baseline, cmd_run, cmd_evaluate, cmd_report):
        rc = fn(args)
        if rc != 0:
            return rc
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="KIS-016 GBrain read-only trial.")
    ap.add_argument("command", choices=["export", "questions", "baseline", "manual-template",
                                        "run", "evaluate", "report", "all"])
    ap.add_argument("--vault-dir", default=DEFAULT_VAULT)
    ap.add_argument("--out-dir", default=DEFAULT_OUT_DIR)
    ap.add_argument("--questions", default=None)
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--adapter", choices=["mock", "manual", "subprocess"], default="mock")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--no-gbrain", action="store_true")
    ap.add_argument("--fail-on-leakage", action="store_true")
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--gbrain-binary", dest="gbrain_binary", default="gbrain",
                    help="Path to the real gbrain CLI (subprocess adapter)")
    args = ap.parse_args()
    return {
        "export": cmd_export, "questions": cmd_questions, "baseline": cmd_baseline,
        "manual-template": cmd_manual_template, "run": cmd_run, "evaluate": cmd_evaluate,
        "report": cmd_report, "all": cmd_all,
    }[args.command](args)


if __name__ == "__main__":
    raise SystemExit(main())
