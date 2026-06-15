# KIS-014 — Acceptance Report

```
KIS-014 completed
tests: 88/88 green (27 new: policy/store/cli/obsidian/immutability)
cards_total: 83
queue_inbox: 81
queue_reviewed: 0
queue_canonical: 1
queue_archived: 1
queue_deferred: 0
queue_rejected: 0
immutability: pass   (review never changes source/content/enrichment/linkage/safety/derived)
obsidian_render: pass (## Review block; pending shown for unreviewed)
dry_run: pass        (--dry-run never writes)
idempotency: pass    (repeat decision = no-op; optimistic version guard)
```

## 5 条验收口径

| 验收项 | 结果 |
|---|---|
| 生命周期闭环 | ✅ inbox/reviewed/canonical/archived/deferred/rejected 受策略表控制流转 |
| 人工闸门 | ✅ canonical 只能 `reviewed --approve` 显式产生；`inbox -> canonical` 实测被拒 |
| 不污染事实源 | ✅ `assert_review_only` 锁定 6 个事实/派生字段；immutability 测试通过 |
| 可审计 | ✅ 每次决策记 previous/next/decision/reason/reviewer/reviewed_at + source/derived/review hash |
| 可复现 | ✅ CLI / store / Obsidian / 88 测试全部离线可验证，零网络零 LLM |

## 实测命令（节选）

```
review_cards.py mark-reviewed --card-id kc_a6faf3d648af507c --reason "verified source and relevance"
  -> reviewed: inbox -> reviewed
review_cards.py approve --card-id kc_a6faf3d648af507c --reason "promote to canonical after human review"
  -> approve_canonical: reviewed -> canonical
review_cards.py archive --card-id kc_d0afc3ec2f1cf81f --reason "low relevance after review"
  -> archive: inbox -> archived
review_cards.py approve --card-id <inbox card> --reason "should fail"
  -> review refused: transition not allowed: inbox -> canonical
```

## 边界确认（本阶段未做，符合要求）
未引入：GBrain / MemOS / Web UI / 自动 canonical / 外部抓取 / 真实 OpenAI review / 批量自动 approve / DPMS 事件导入。

## 设计说明
- 生命周期状态字段沿用既有 `lifecycle.state`（未新增 `status` 以免双字段不一致）；
  `review.previous_status/next_status` 记录迁移。`lifecycle.version` 作乐观锁。
- blocked 卡片从不进 store，故从不进队列。
