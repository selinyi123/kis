# KIS-016 — GBrain Read-Only Trial

验证 GBrain 能否作为 Obsidian 的**派生索引层**，在**不污染事实源、不泄漏敏感、不制造第二
事实源**的前提下，提升跨项目检索与证据化问答能力。本阶段是**只读试点**，不是生产接入。

## 流程
```
export(安全快照) → questions(20) → baseline(离线对照) → run(adapter) → evaluate → report
```

## CLI
```powershell
python scripts/gbrain_trial.py export --vault-dir "...\KIS 知识情报系统" --dry-run
python scripts/gbrain_trial.py all --adapter mock        # 全离线跑通
python scripts/gbrain_trial.py run --adapter manual      # 回放真实 GBrain 的 JSONL
python scripts/gbrain_trial.py run --adapter subprocess  # 本机装了 gbrain CLI 才用；缺失则优雅降级
python scripts/gbrain_trial.py evaluate --fail-on-leakage
python scripts/gbrain_trial.py report
```
flags：`--vault-dir --out-dir --questions --limit --adapter --dry-run --no-gbrain --fail-on-leakage`。

## Adapters（GBrain 永不硬依赖）
- **mock**：离线确定性（baseline 支撑），测试用 —— 验证 harness/安全/可追溯，**不能**回答"GBrain 是否优于 baseline"（它就是 baseline）。
- **manual**：人工用真实 GBrain 跑完后把结果 JSONL 放入 `runs/latest/gbrain_manual_input.jsonl` 再评测。
- **subprocess**：本机 `gbrain` CLI 存在则调用；缺失抛 `AdapterUnavailable`，主流程降级为 baseline+report。

## 产物（`.kis/gbrain_trial/`，gitignored，非事实源）
`exported_vault/ · manifests/{export_manifest,denied_files,content_hashes}.json ·
questions/questions.jsonl · runs/latest/{baseline_results,gbrain_results}.jsonl,
evaluation.json, relation_audit.json, leakage_audit.json, trial_report.md`

## 评估指标
citation_traceability · missing_source_rate · unknown_when_no_source_rate ·
sensitive_leakage_count · wrong_relation_count · conflict/stale counts ·
baseline_overlap · answer_usefulness_score。

## 边界
GBrain 只读快照；不写 Obsidian/store/lifecycle/review/canonical；输出仅进 trial artifacts。
真实 GBrain 失败不破坏主流程。安全策略见 [KIS-016_SENSITIVE_FILTER_POLICY.md](KIS-016_SENSITIVE_FILTER_POLICY.md)。

## 判断分叉（真实 GBrain 跑完后）
A 通过 → KIS-017 Prompt Engine memory benchmark；B 部分通过 → 保持 read-only，扩问题集/过滤；
C 不通过 → 拒绝进主架构，保留 Obsidian + Dashboard + baseline search。
