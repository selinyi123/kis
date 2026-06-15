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
