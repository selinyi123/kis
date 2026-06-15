# KIS-015 — Review Dashboard（只读 Obsidian 审阅看板）

把 KIS-014 的审阅队列做成**可浏览、可筛选、可决策辅助**的静态 Markdown 看板。
**只读视图层**：只展示/排序/分组/给出建议命令，绝不改 store、不改 lifecycle/review、不自动 approve。

## 构建

```powershell
python scripts/build_review_dashboard.py                       # 全量 -> vault_out/Dashboards/
python scripts/build_review_dashboard.py --obsidian-dir "D:\TOOL\OBSIDIAN\Home\prompt仓库\KIS 知识情报系统"
python scripts/build_review_dashboard.py --dry-run             # 只列文件+统计，不写盘
python scripts/build_review_dashboard.py --only inbox          # 单页
python scripts/build_review_dashboard.py --only stats
python scripts/build_review_dashboard.py --limit 50
```

## 页面（输出到 `<obsidian-dir>/Dashboards/`）

| 文件 | 内容 |
|---|---|
| KIS Review Dashboard.md | 总览：Summary 表 + Priority Queues + 链接 |
| Review Inbox.md | 所有 inbox，按 critical>hot>warm>cold、integrate>...>ignore、newer first 排序；**建议命令仅 mark-reviewed/defer/archive（无 approve）** |
| Canonical Candidates.md | 仅 `reviewed` + (critical\|hot) + (integrate\|test)；建议命令 `approve`（人工） |
| Archive Candidates.md | next_action==archive ∨ value_level==cold ∨ state==rejected；排除 canonical/archived |
| Deferred Queue.md | state==deferred；建议 mark-reviewed / archive |
| Rejected Queue.md | state==rejected；**仅审计回看，无 approve** |
| Review Stats.md | 按 lifecycle/source_type/category/value_level/next_action/project_relevance/sensitivity/generated_day |

## 模块

`src/kis/dashboard/`：`models`（页名/排名常量）、`selectors`（纯函数选择/排序）、
`stats`（统计）、`commands`（建议命令，inbox 永不含 approve）、`render`（Markdown，转义/缺失兜底）。
CLI：`scripts/build_review_dashboard.py`。只读 store 方法：`store.load_dashboard_cards()`。

## 边界
看板是视图层不是事实源；状态变更一律走 `scripts/review_cards.py`（KIS-014）。
每页带 `generated_at` + `generator` 版本；除时间戳外输出确定、可 diff。全程离线。
