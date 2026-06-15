# KIS-014 — Review Queue（人工确认队列）

把 KIS-013 的 derived（模型建议）送入人工确认闭环。**derived 是建议，canonical 是事实**，
二者分层；canonical 只能由人显式产生。

## CLI

```powershell
python scripts/review_cards.py list
python scripts/review_cards.py list --status inbox
python scripts/review_cards.py list --value-level hot --next-action integrate
python scripts/review_cards.py show --card-id <id>
python scripts/review_cards.py mark-reviewed --card-id <id> --reason "verified source and relevance"
python scripts/review_cards.py approve      --card-id <id> --reason "promote to canonical after human review"
python scripts/review_cards.py archive      --card-id <id> --reason "low relevance after review"
python scripts/review_cards.py defer        --card-id <id> --reason "revisit later"
python scripts/review_cards.py reject       --card-id <id> --reason "not useful"
python scripts/review_cards.py export --status canonical --format md
```

写操作通用参数：`--dry-run`（不落库）、`--db-path`、`--obsidian-dir`、`--limit`、`--reviewer`（默认 human）。
过滤：`--status / --value-level / --next-action / --source-type / --category`。

## 流程

```
enrich (derived) ──▶ review_cards list ──▶ 人工核对 source + relevance
   ──▶ mark-reviewed ──▶ approve(canonical) | archive | defer | reject
```

## 模块

| 文件 | 职责 |
|---|---|
| `src/kis/review/policy.py` | 合法迁移表、decision→status、锁定字段、`assert_review_only` |
| `src/kis/review/models.py` | source_hash / derived_hash / review_hash（确定性） |
| `src/kis/review/actions.py` | `apply_review`（纯函数，幂等，写 lifecycle+review） |
| `src/kis/review/queue.py` | `filter_cards` / `queue_counts`（blocked 排除） |
| `src/kis/review/export.py` | 队列导出 md/json |
| `src/kis/store.py` | `get_card` / `list_review_candidates` / `save_review`（乐观锁） |
| `scripts/review_cards.py` | CLI |

Obsidian 每张卡片追加 `## Review` 区块（未审阅显示 Status: inbox / Decision: pending），
**不改写 Source / Extraction / Derived**。
