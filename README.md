# KIS — Knowledge Intelligence System

多源个人知识情报系统。把分散在 GitHub Stars / 剪切板 / 网页 / X / 知乎 / B站 / 小红书 / 本地文档的信息流，沉淀为**可搜索、可同步、可被 AI / Codex 调用**的结构化知识资产。

> 不是更大的收藏夹，而是一个**知识运行时引擎**：采集 → 清洗 → 去重 → 摘要 → 分类 → 打标 → 价值评分 → 主题聚类 → 项目关联 → 更新跟踪 → 同步归档。

## 当前状态：v0.3.1 三源 + AI 派生层 + 人工确认队列 ✅

三个源：**GitHub Stars + 浏览器书签 + 单 URL 网页剪藏 → KnowledgeCard → SQLite(FTS5) → Obsidian**，叠加 **AI 派生加工层**（摘要/评分/相关度），再叠加 **人工确认队列**（KIS-014）：derived 是建议，canonical 是人工确认的事实。

```powershell
# 审阅闭环：canonical 只能人工 approve 产生
python scripts/review_cards.py list --status inbox
python scripts/review_cards.py mark-reviewed --card-id <id> --reason "verified"
python scripts/review_cards.py approve --card-id <id> --reason "promote after review"   # -> canonical
python scripts/review_cards.py archive|defer|reject --card-id <id> --reason "..."
python scripts/review_cards.py export --status canonical --format md
```
生命周期：`inbox → reviewed → canonical / archived / deferred / rejected`。见 [docs/KIS-014_LIFECYCLE_POLICY.md](docs/KIS-014_LIFECYCLE_POLICY.md)。

只读审阅看板（KIS-015）：
```powershell
python scripts/build_review_dashboard.py --obsidian-dir "D:\TOOL\OBSIDIAN\Home\prompt仓库\KIS 知识情报系统"
python scripts/build_review_dashboard.py --dry-run
```
生成 7 页到 `Dashboards/`（总览/Inbox/Canonical/Archive/Deferred/Rejected/Stats）。看板只读、只给建议命令；状态变更仍走 review CLI。见 [docs/KIS-015_REVIEW_DASHBOARD.md](docs/KIS-015_REVIEW_DASHBOARD.md)。

GBrain 只读试点（KIS-016，验证派生索引层，不污染事实源/不泄敏/不写回）：
```powershell
python scripts/gbrain_trial.py all --adapter mock --vault-dir "D:\TOOL\OBSIDIAN\Home\prompt仓库\KIS 知识情报系统"
```
安全导出快照 → 20 问题 → baseline 对照 → 评估 → `.kis/gbrain_trial/runs/latest/trial_report.md`。GBrain 非硬依赖（mock/manual 离线，subprocess 可选）。见 [docs/KIS-016_GBRAIN_READONLY_TRIAL.md](docs/KIS-016_GBRAIN_READONLY_TRIAL.md)。
> KIS-016R 真实 GBrain（Ollama）跑完 20 问 → **判 B**：安全可用但未跑赢免费 keyword baseline，保持 read-only。

外部 Inbox 摄取（KIS-018，无网络、安全可审计）：
```powershell
python scripts/ingest_external.py github-stars --input exports/stars.json
python scripts/ingest_external.py bookmarks    --input exports/bookmarks.html
python scripts/ingest_external.py web-clips     --input exports/clips.jsonl --dry-run
```
三入口 → secret guard → 去重 → 全部落 `inbox`（不自动 reviewed/canonical）→ Obsidian `External-Inbox/`。见 [docs/KIS-018_EXTERNAL_INBOX_INGESTION.md](docs/KIS-018_EXTERNAL_INBOX_INGESTION.md)。

```
采集: GitHub Stars / Browser Bookmarks / Single Web URL ──▶ KnowledgeCard(v0.3.0)
        ──▶ 分类 / SSRF / blocked 拦截 ──▶ SQLite + 事件日志 ──▶ Obsidian
加工: enrich_cards.py ──▶ derived{summary, value_score, value_level, project_relevance,
        next_action, review_flags, generator(可复现溯源)}   # 只写 derived，永不改 source
```

加工：
```powershell
python scripts/enrich_cards.py --mode heuristic                      # 确定性基线（离线）
python scripts/enrich_cards.py --mode auto --provider mock           # 优先 LLM，失败降级
python scripts/enrich_cards.py --mode llm --provider openai --limit 10
python scripts/enrich_cards.py --mode heuristic --dry-run            # 不落库预览
```
派生层安全边界见 [docs/KIS-013_PROMPT_INJECTION_BOUNDARY.md](docs/KIS-013_PROMPT_INJECTION_BOUNDARY.md)。

## 快速开始

```powershell
# 1) 运行单元测试（纯逻辑，无需网络）
python -m unittest discover -s tests -v

# 2) 采集你的 GitHub Stars（复用已登录的 gh CLI，无需配置 token）
python scripts/ingest_github_stars.py

# 3) 导入浏览器书签（Netscape HTML 导出）
python scripts/ingest_bookmarks.py "C:\Users\<you>\Documents\bookmarks.html"

# 4) 剪藏单个网页 URL（SSRF 安全，轻量 stdlib 提取）
python scripts/ingest_url.py https://example.com/article

# 可选：用 Crawl4AI 后端增强正文提取（需 pip install crawl4ai；缺失时 auto 自动降级 stdlib）
python scripts/ingest_url.py https://example.com/article --extractor auto      # 优先 crawl4ai，失败降级
python scripts/ingest_url.py https://example.com/article --extractor crawl4ai  # 强制 crawl4ai（缺失则明确报错）

# 仅入库不导出 Obsidian
python scripts/ingest_github_stars.py --no-obsidian

# 导出到真实 Obsidian 库
python scripts/ingest_bookmarks.py bookmarks.html --obsidian-out "D:\TOOL\OBSIDIAN\Home\prompt仓库\KIS 知识情报系统"
```

产物：`data/kis.db`（SQLite，含 cards / events / cards_fts）+ `vault_out/`（Obsidian 笔记，均 gitignored）。

## 目录结构

```
schema/knowledge-card.schema.json   统一知识卡片契约（v0.1.0 冻结）
src/kis/card.py                     卡片构建 + 确定性身份(stable_id/content_hash) + 项目关联
src/kis/validate.py                 零依赖 JSON-Schema 校验（拒绝未知字段）
src/kis/store.py                    SQLite + FTS5 + 幂等 upsert + 事件日志
src/kis/obsidian.py                 卡片 → Obsidian 笔记（frontmatter + wikilink）
scripts/ingest_github_stars.py      GitHub Stars 连接器（v0.1 参考实现）
examples/github-star.sample.json    示例卡片
tests/test_pipeline.py              闭环测试（11 项）
docs/                               PRODUCT_SPEC / ARCHITECTURE / ROADMAP / HANDOFF
```

## 设计原则（继承自 DPMS / PPE / ClipVault）

- **零运行时第三方依赖**（纯 stdlib，ClipVault 纪律）。
- **schema 即契约**：未知字段一律拒绝（PPE）。
- **确定性与 LLM 分离**：清洗/去重/身份是确定性纯函数；摘要/标签/评分（LLM）在 v0.2。
- **幂等事实源**：`stable_id` 主键 + `content_hash` 变更检测 + 事件日志（DPMS Event Store / ClipVault outbox）。

详见 [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) 与 [调研报告与落地蓝图](KIS_调研报告与落地蓝图_20260614.md)。
