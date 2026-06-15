# KIS-016 — Acceptance Report

```
KIS-016 completed
tests: 148/148 green (35 new: filters/exporter/manifest/questions/baseline/adapter/evaluator/report/cli/safety)
questions_total: 20
exported_files: 96
denied_files: 0           (real KIS vault has no sensitive files; deny power proven by unit tests)
baseline_results: 20
gbrain_adapter: mock      (real GBrain NOT installed — subprocess degraded gracefully)
citation_traceability: 1.0
missing_source_rate: 0.0
sensitive_leakage_count: 0
wrong_relation_count: 0
store_immutability: pass
obsidian_immutability: pass  (source vault byte-for-byte unchanged after export)
no_writeback: pass
no_auto_canonical: pass
trial_report: pass
decision: keep_readonly   (harness + safety ready; real-GBrain vs baseline verdict pending)
```

## 6 条验收口径

| 验收项 | 结果 |
|---|---|
| 只读隔离 | ✅ GBrain 只读 `.kis/gbrain_trial/exported_vault/` 安全快照，从不读原始 vault |
| 敏感过滤 | ✅ secret/blocked/confidential/DPMS 凭据(cookie/token/profile/qr/session)/`.env`/`.db`/.key 全部拒绝（单测验证 denied≥6） |
| 20 问题集 | ✅ 覆盖三项目、跨项目关系、生命周期、敏感边界 |
| Baseline 对照 | ✅ 离线关键词/CJK-bigram 搜索作对照（baseline_results.jsonl） |
| 引用可追溯 | ✅ citation_traceability=1.0，答案只引用导出内文件（path+snippet） |
| 错误审计 | ✅ relation_audit / leakage_audit / 缺源率 / 冲突 / 过期 指标齐全 |
| 不写回 | ✅ 源 vault 导出前后字节级一致；不改 store/lifecycle/review |
| 不 canonical | ✅ trial 不产生 canonical（allow_canonical=no） |
| 可复现 | ✅ mock/manual 离线可跑，subprocess 可选且缺失优雅降级；148 测试全绿 |
| 报告导向 | ✅ 仅输出 trial_report.md，不做生产决策 |

## 重要诚实说明
1. **mock 是 baseline 支撑的**：因此 `baseline_overlap=1.0`、`promote_to_kis017=yes` 反映的是
   **试点框架与安全性已就绪**，**不是**"GBrain 显著优于 baseline"的真实结论。真正的 A/B/C 判断
   必须在**真实 GBrain**（manual 或 subprocess）跑完 20 问题后再下。本机未安装 GBrain，故记录为
   `keep_readonly`，真实对比待补。
2. **denied=0**：真实 KIS vault 仅含公开/internal 笔记与卡片，无敏感文件 —— 这是预期。过滤器的
   排除能力由 35 个单测（含 secret/token/cookie/qr/.env/.db 的临时 vault，denied≥6）证明。
3. 试点期间引入并修复两处真实缺陷：① 泄漏检测从"词汇子串"改为"真实密钥模式 + 越界引用"
   （消除 author→auth 假阳性）；② 二进制判定改为只看 NUL 字节（修正截断 UTF-8 中文 .md 被误判
   binary，included 94→96）。

## 边界确认（未做，符合要求）
未引入：生产接入 / 自动写回 / 自动 canonical / MemOS / 外部数据入口 / 把 GBrain 当事实源。

---

# KIS-016R — Real GBrain Quality Run（状态：BLOCKED / PENDING）

```
KIS-016R status: BLOCKED — real GBrain not available on this machine
real_gbrain: NOT EXECUTED
  - PATH:  no `gbrain` binary
  - pip:   no `gbrain` package
  - npm:   no global gbrain
  - subprocess adapter attempted -> AdapterUnavailable -> graceful degrade (baseline/report only)
questions_total: 20 (prepared)
exported_files: 96 · baseline_results: 20 · manual_template: ready (20 stubs)
citation_traceability: pending (no real answers)
sensitive_leakage_count: pending
wrong_relation_count: pending
baseline_overlap: pending
answer_usefulness_score: pending
decision: PENDING  (NOT A/B/C — a real-GBrain verdict requires real GBrain output)
next: 提供真实 GBrain 结果后评测（二选一，见下）
```

## 为什么没有 A/B/C
A/B/C 必须基于**真实 GBrain** 对 20 问题的回答。本机无任何可调用的 GBrain，**执行 Agent 不会
伪造 GBrain 答案**（伪造将违背"GBrain 输出不能当事实源 / 可复现"，并使决策失真）。因此 KIS-016R
冻结为 PENDING，KIS-016 的 keep_readonly 决策维持不变。

## 已就绪的两条补全路径（拿到真实 GBrain 即可一键评测）
**路径一 · subprocess（本机装了 GBrain CLI）**
```
python scripts/gbrain_trial.py export
python scripts/gbrain_trial.py baseline
python scripts/gbrain_trial.py run --adapter subprocess --limit 20
python scripts/gbrain_trial.py evaluate --fail-on-leakage
python scripts/gbrain_trial.py report
```
**路径二 · manual（在别处用真实 GBrain 跑，回填结果）**
```
python scripts/gbrain_trial.py export
python scripts/gbrain_trial.py baseline
python scripts/gbrain_trial.py manual-template      # 生成 20 题 stub JSONL
# 用真实 GBrain 回答 20 题，把 answer/citations 填入：
#   .kis/gbrain_trial/runs/latest/gbrain_manual_input.jsonl
python scripts/gbrain_trial.py run --adapter manual
python scripts/gbrain_trial.py evaluate --fail-on-leakage
python scripts/gbrain_trial.py report
```
评测产物：`.kis/gbrain_trial/runs/latest/{evaluation.json, relation_audit.json, leakage_audit.json, trial_report.md}`。

## 决策标准（评测后据此判 A/B/C）
- **A 进 KIS-017**：citation_traceability ≥ 0.95 且 leakage == 0 且 wrong_relation ≤ 1 且
  missing_source_rate ≤ 0.10 且 usefulness 明显高于 baseline。
- **B 保持 read-only**：traceability 合格但 usefulness 提升不明显 / 少量错误关系 / 冲突陈旧提示不足 /
  baseline_overlap 过高（增益有限）。
- **C 放弃 GBrain**：leakage > 0 / 引用导出目录外内容 / 大量无来源断言 / 错误关系污染 / 不能稳定复现。

## KIS-016R 新增（真实交付，非伪造）
`scripts/gbrain_trial.py manual-template`（生成可回填的 20 题 stub）+ 对应测试。其余安全/框架不变。

## KIS-016R 真实 GBrain 安装进度（2026-06-15，用户授权"装到导入为止"）
**已完成（key-free）：**
- 装 **Bun 1.3.14**（`~/.bun`）+ **gbrain 0.42.44**（`bun install -g github:garrytan/gbrain`，binary `~/.bun/bin/gbrain.exe`）。
- `gbrain init --pglite --no-embedding` 建脑（PGLite，**未开 cron/daemon**）。脑库在 GBrain 全局位置（不在 repo，不在 .kis）。
- `gbrain import <staged> --no-embed` 导入 **96 页 / 262 chunks**（0 错误）。
- 真实 CLI 已摸清：`import <dir>` / `query <q>` / `search <q>`（输出 `[score] slug -- snippet`，无 `--json`）。
- 已把 `SubprocessGBrainAdapter` 重写为真实 `gbrain query` + 解析器；`evaluator` 加 slug↔path 归一化；**150/150 pytest**。

**踩坑修复：** GBrain 的 `import` 在含空格路径（`Work Program`）下 `collect_files=0`；改为复制到无空格暂存目录后导入成功（96/96）。

**停在这里（付费门槛）：** `gbrain config` 显示 embedding_model 默认 `zeroentropyai:zembed-1`，但**未配 key** → `gbrain embed --all` 与语义 `query` 无法运行。这正是用户要停下等 key 的"付费查询"步。

**给 key 后一键完成（我来跑）：**
1. 用户设嵌入 provider key（任一）：`ZEROENTROPY_API_KEY` / 或切 `gbrain config set embedding_model openai:text-embedding-3-large` + `OPENAI_API_KEY` / 或 `VOYAGE_API_KEY`。
2. 我跑：`gbrain embed --all`（嵌入 96 页，付费）→ `gbrain query` 跑 20 题 → `scripts/gbrain_trial.py run --adapter subprocess`(指向真实 binary)→ `evaluate --fail-on-leakage` → `report` → 据指标给 **A/B/C**。

