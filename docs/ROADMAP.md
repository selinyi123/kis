# KIS 路线图 ROADMAP

| 版本 | 目标 | 退出标准 |
|---|---|---|
| **v0.1 ✅** | 多源采集框架雏形 + 知识卡片 + 项目关联 + Obsidian 同步 | Stars 源跑通，幂等、可搜、可同步 |
| v0.2 | LLM 加工管道 + 注入审计 + 网页/剪切板源 + 近似去重 | 入库即摘要/打标/评分(标证据等级) |
| v0.3 | X/知乎/B站/小红书 + 更新跟踪 + MemOS 迁移 | 6+ 源，可被 AI 调用(MCP/CLI) |
| v0.4 | codegraph 服务 Codex + 主题聚类 + Web 控制台 | Codex 可检索 KIS |
| v1.0 | 自动研究报告 + 任务生成 + 知识图谱 | 输入主题→grounded 综述+任务 |
| v2.0 | 视频/图文解析 + Agent 调用 | 多模态入库 |

## v0.1 任务包状态（P0/P1/P2）

### P0（已完成）
- [x] KIS-002 冻结 KnowledgeCard v0.1 schema + 零依赖校验 + 迁移位
- [x] KIS-004 GitHub Stars 连接器（37 star 实测幂等入库）
- [x] KIS-005 SQLite + FTS5 + 事件 outbox
- [x] KIS-006 Obsidian 同步（frontmatter + wikilink）
- [x] KIS-010(部分) 规则化项目关联（infer_projects）
- [ ] KIS-001 在 GitHub 建私有 `kis` repo 并首推（待用户授权 push）
- [ ] KIS-003 BaseConnector 抽象类化（当前为脚本形态，已具雏形）

### v0.2a（已完成）
- [x] KIS-007 浏览器书签连接器（Netscape HTML → KnowledgeCard，分类/敏感拦截/Obsidian 分目录）
- [x] schema 演进 0.1.0 → 0.2.0（source_type / 来源溯源字段 / authority / sensitivity）
- [x] 分类规则引擎 `classify.py`（blocked 拦截：成人/机场/免税地址/反检测）

### v0.2b（已完成）
- [x] KIS-008 单 URL 网页剪藏：`python scripts/ingest_url.py <url>`（SSRF 防线 + stdlib 提取 + 分类 + Web-Clips 分目录 + blocked 日志）
- [x] schema 演进 0.2.0 → 0.2.1（web-clip 字段）

### v0.2c（已完成）
- [x] KIS-009 Crawl4AI 可选增强（extractors 抽象：stdlib 基线 + crawl4ai 可选 adapter；延迟导入、非硬依赖、auto 降级、forced 明确报错）
- [x] schema 演进 0.2.1 → 0.2.2（extraction 溯源 + clean_markdown/structured_data）

### P1（后续）
- [ ] KIS-008b 剪切板源接入（对接 ClipVault outbox）
- [ ] KIS-009b 标签体系数据文件 `taxonomy.json` 驱动
- [ ] KIS-011 近似去重（simhash/embedding）
- [ ] KIS-012 GitHub JSONL 私备

### v0.3.0（已完成）
- [x] KIS-013 AI 派生加工层：摘要 + 价值评分(0-1) + value_level + project_relevance + next_action + review_flags
  * 013a 确定性 heuristic 基线（offline）；013b 可选 LLM provider（mock/openai，延迟导入）
  * schema 0.3.0 加 `derived`；prompt 注入边界文档；derived 永不改 source（assert_only_derived）
  * `enrich_cards.py --mode heuristic|llm|auto --provider --limit --dry-run --force --source-type --category`

### v0.3.1（已完成）
- [x] KIS-014 Review Queue / Human Confirmation Gate：inbox→reviewed→canonical/archived/deferred/rejected
  * `src/kis/review/`（policy/models/actions/queue/export）+ `scripts/review_cards.py`
  * canonical 仅人工 approve；review 只写 lifecycle+review；blocked 不入队；幂等 + 乐观锁；离线
  * schema 0.3.1（lifecycle.state 扩展 + 可选 review 审计对象）

### v0.3.2（已完成）
- [x] KIS-015 Review UI / Obsidian Dashboard：7 页只读看板（总览/Inbox/Canonical/Archive/Deferred/Rejected/Stats）
  * `src/kis/dashboard/`（selectors/stats/commands/render）+ `scripts/build_review_dashboard.py`
  * 只读（不改 store/lifecycle/review）；Inbox 零 approve；canonical 候选仅来自 reviewed；dry-run/幂等/离线

### 下一阶段（用户定）
- [ ] KIS-016 GBrain read-only trial
- [ ] KIS-017 Memory benchmark via Prompt Engine
- [ ] KIS-018 External inbox ingestion
- [ ] MemOS 隔离实验

### 其它待办
- [ ] KIS-008b 剪切板源（对接 ClipVault outbox）
- [ ] KIS-011 近似去重（simhash/embedding）
- [ ] KIS-012 GitHub JSONL 私备

### P2
- [ ] KIS-013 价值评分 v1（DPMS scoring 改造）
- [ ] KIS-014 更新跟踪（pushed_at/release → stale）
- [ ] KIS-015 CLI：kis add/search/recall/sync
- [ ] KIS-016 注入审计闸门（移植 PPE adversarial_cases）
