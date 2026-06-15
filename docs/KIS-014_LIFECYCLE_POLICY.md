# KIS-014 — Lifecycle Policy（生命周期策略）

生命周期状态存放在 `lifecycle.state`（即"生命周期状态字段"；KIS-014 复用它，未新增 `status`
以避免双字段不一致）。`lifecycle.version` 用作乐观锁。

## 状态

```
inbox      新采集/已加工，待人工审阅
reviewed   人工已审阅，候选 canonical
canonical  人工确认的权威知识（仅由显式 approve 产生）
archived   审阅后归档（低价值/已过时）
deferred   暂缓，稍后再看
rejected   驳回
```

## 合法迁移

```
inbox    -> reviewed | archived | deferred | rejected
reviewed -> canonical | archived | deferred | rejected
deferred -> inbox | reviewed | archived | rejected
canonical / archived / rejected : 终态（本阶段不自动降级）
```

## 明确禁止

```
inbox     -> canonical      （不允许跳过审阅）
archived  -> canonical
rejected  -> canonical
canonical -> inbox
canonical -> reviewed
```

> 本阶段不实现 `--force`。canonical 只能从 reviewed 经显式 `approve` 命令产生。

## decision → 状态

| CLI 命令 | decision | 结果状态 |
|---|---|---|
| mark-reviewed | reviewed | reviewed |
| approve | approve_canonical | canonical |
| archive | archive | archived |
| defer | defer | deferred |
| reject | reject | rejected |

## 不可逾越的边界

1. AI/derived 永不自动提升 canonical。
2. review 只写 `lifecycle` + `review`（`assert_review_only` 锁定
   source/content/enrichment/linkage/safety/derived）。
3. 每次决策审计：previous_status / next_status / decision / reason / reviewer /
   reviewed_at / source_hash / derived_hash / review_hash。
4. blocked 卡片不得进入队列。
5. reason 不能为空；reviewer 默认 `human`。
6. 同一操作幂等（current == target 时为 no-op）；写入用乐观版本锁。
