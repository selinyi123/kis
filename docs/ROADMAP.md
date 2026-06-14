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

### P1（v0.2b 起）
- [ ] KIS-008 单 URL 网页剪藏：`python scripts/ingest_url.py <url>`
- [ ] KIS-009 Crawl4AI 可选增强（URL → 干净 markdown/json）
- [ ] KIS-008b 剪切板源接入（对接 ClipVault outbox）
- [ ] KIS-009b 标签体系数据文件 `taxonomy.json` 驱动
- [ ] KIS-011 近似去重（simhash/embedding）
- [ ] KIS-012 GitHub JSONL 私备

### P2
- [ ] KIS-013 价值评分 v1（DPMS scoring 改造）
- [ ] KIS-014 更新跟踪（pushed_at/release → stale）
- [ ] KIS-015 CLI：kis add/search/recall/sync
- [ ] KIS-016 注入审计闸门（移植 PPE adversarial_cases）
