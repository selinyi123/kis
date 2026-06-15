# KIS-018 — External Inbox Ingestion

把外部资料以统一 KnowledgeCard 形式安全送入 inbox：

```
external file → adapter(parse) → safety(secret guard) → normalize(card) →
dedupe → store(inbox) → Obsidian External-Inbox → KIS-014 Review Queue
```

不是大规模抓取，而是**安全、可审计、可复现**的摄取 MVP。边界见
[KIS-018_SOURCE_BOUNDARY.md](KIS-018_SOURCE_BOUNDARY.md)。

## CLI
```powershell
python scripts/ingest_external.py github-stars --input exports/stars.json --dry-run
python scripts/ingest_external.py github-stars --input exports/stars.json
python scripts/ingest_external.py bookmarks    --input exports/bookmarks.html
python scripts/ingest_external.py web-clips     --input exports/clips.jsonl
python scripts/ingest_external.py report
```
通用参数：`--db-path --obsidian-dir --dry-run --limit --source-project --category --force --report-path`（`--force` 默认关闭）。

## 模块（`src/kis/ingest/`）
| 文件 | 职责 |
|---|---|
| `safety.py` | 密钥/凭据扫描（sk-/ghp_/AKIA/PRIVATE KEY/xxx=/.env/otp）→ blocked |
| `normalizer.py` | raw → KnowledgeCard（复用 `card.py` 构建器，统一 schema，落 inbox） |
| `dedupe.py` | normalized_url / content_hash / (source_type,source_id) + store 只读校验 |
| `github_stars.py / bookmarks.py / web_clips.py` | 三个解析器（无网络） |
| `runner.py` | 编排 + 计数；`report.py` 报告（JSON + Markdown） |
| `scripts/ingest_external.py` | CLI |

复用：`card.github_star_card` / `connectors.bookmarks` 解析器 / `classify`（书签分类+blocked）/ `store.upsert`（幂等）/ `obsidian.render_external_inbox_md`。

## 产物
- 卡片：`lifecycle.state=inbox`，`review` 缺省=pending。
- Obsidian：`External-Inbox/{GitHub-Stars,Browser-Bookmarks,Web-Clips}/`，每卡含
  Source/Content/Safety/Lifecycle/Review + 建议命令（mark-reviewed/archive/defer/reject，**无 approve**）。
- 报告：`data/ingest_reports/<source>_<ts>.{json,md}` + `latest.json`（dashboard 读取）。
- Dashboard：Review Stats 增 External Inbox（total / by source_type / by project）+ Last Ingest Run。

## 实测（fixtures）
github_star: seen4 created2 dup1 blocked1 ｜ web_bookmark: seen5 created3 dup1 blocked1 ｜
web_clip: seen5 created1 dup1 blocked1 errors2。dry-run 与真实计数一致。
