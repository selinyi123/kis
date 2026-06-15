# KIS 产品规格 PRODUCT_SPEC

## 1. 使命
把分散在多平台的个人信息流，沉淀为**可搜索、可同步、可被 AI/Codex 调用、可服务项目规划与研究决策**的个人知识资产中枢。核心区别于收藏夹：每条信息进入明确的**知识生命周期**。

## 2. 用户与场景
单用户（架构师/开发者，selinyi123），个人自用、非商业。场景：
- 把 GitHub Stars / 网页 / 剪切板 / 社交收藏统一归档为知识卡片。
- 用自然语言/标签/项目维度检索过往知识。
- 让 Codex/Claude 在开发时直接调用相关知识。
- 周期性产出主题研究综述、吸收进项目路线图。

## 3. 输入源（连接器）
GitHub Stars（v0.1✅）、网页剪藏、剪切板(ClipVault)、Twitter/X 书签、知乎收藏、B站收藏、小红书收藏、本地文档、RSS。

## 4. 统一产物：KnowledgeCard
版本化 schema（见 `schema/knowledge-card.schema.json`，v0.1.0 冻结）。七大域：source / content / enrichment / linkage / lifecycle / safety + 顶层身份。

## 5. 知识生命周期
`inbox → cleaned → enriched → linked → archived`，旁路 `quarantine`（注入/密钥命中）与 `stale`（源更新）。每次迁移写事件日志。

## 6. 功能需求（按版本）
- **v0.1（已交付）**：多源采集框架雏形（Stars 连接器）、KnowledgeCard 冻结、确定性去重/身份、SQLite+FTS 存储、Obsidian 同步、规则化项目关联。
- **v0.2**：LLM 摘要/分类/打标/价值评分（标证据等级）、注入审计闸门、网页剪藏(crawl4ai)、剪切板源接入、近似去重。
- **v0.3**：X/知乎/B站/小红书连接器、更新跟踪、MemOS 记忆迁移、MCP/CLI 对外。
- **v0.4**：codegraph 服务 Codex、主题聚类、Web 控制台。
- **v1.0**：自动研究报告、任务生成、知识图谱。
- **v2.0**：视频/图文解析、Agent 调用。

## 7. 非功能需求
- 零运行时第三方依赖（核心）。
- 幂等：重复采集不产生重复卡片。
- 可复盘：事件日志为事实源。
- 安全：密钥不入库不外发（Secret Guard，v0.2）；外部内容喂 LLM 前过注入审计（v0.2）。
- 合规：仅处理用户自己已收藏的公开内容，限速，命中验证码即停。

## 8. 验收（v0.1 DoD）
见 ROADMAP.md / HANDOFF.md。当前 11 项单测全绿、37 个 star 实测入库幂等、FTS 可搜、Obsidian 可同步。
