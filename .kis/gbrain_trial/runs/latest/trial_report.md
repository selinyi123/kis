# KIS-016 GBrain Read-Only Trial Report

_generated_at: 2026-06-15T01:36:07Z · adapter: mock · real_gbrain_executed: False_

## Summary

| Metric | Value |
|---|---:|
| Questions | 20 |
| Exported files | 96 |
| Denied files | 0 |
| Citation traceability | 1.0 |
| Missing-source rate | 0.0 |
| Unknown-when-no-source rate | 1.0 |
| Sensitive leakage count | 0 |
| Wrong relation count | 0 |
| Conflicts flagged | 0 |
| Stale warnings | 0 |
| Baseline overlap | 1.0 |
| Answer usefulness (0-1) | 0.78 |

## Export Scope

- Source vault: `D:/TOOL/OBSIDIAN/Home/prompt仓库/KIS 知识情报系统`
- Included: 96 files, 303814 bytes

## Denied Files

_(none)_

## Questions

20 trial questions (see questions.jsonl).

## Baseline vs GBrain

Baseline = offline keyword/FTS search; GBrain = derived index under test.
Per-question scores in evaluation.json.

## Citation Traceability

1.0 of answers cite only files present in the export.

## Gaps / Conflicts / Stale Data

- conflicts flagged: 0
- stale warnings: 0

## Entity Relation Audit

- unsupported relations: 0 (none)

## Sensitive Leakage Audit

- leakage incidents: 0 (none)

## Failures

_(none)_

## Decision

- promote_to_kis017: yes
- keep_readonly: yes
- allow_writeback: no
- allow_canonical: no
