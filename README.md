# KIS — Knowledge Intelligence System

多源个人知识情报系统。把分散在 GitHub Stars / 剪切板 / 网页 / X / 知乎 / B站 / 小红书 / 本地文档的信息流，沉淀为**可搜索、可同步、可被 AI / Codex 调用**的结构化知识资产。

> 不是更大的收藏夹，而是一个**知识运行时引擎**：采集 → 清洗 → 去重 → 摘要 → 分类 → 打标 → 价值评分 → 主题聚类 → 项目关联 → 更新跟踪 → 同步归档。

## 当前状态：v0.2c 三源 + 可选提取后端 ✅

三个源：**GitHub Stars + 浏览器书签 + 单 URL 网页剪藏 → KnowledgeCard → SQLite(FTS5) → Obsidian Note**，幂等、可搜索、自动分类、敏感项拦截、SSRF 防线、自动项目关联。单 URL 剪藏支持可插拔提取后端（**stdlib 基线默认，Crawl4AI 可选增强**）。

```
源连接器 ──▶ KnowledgeCard(v0.2.2 schema) ──▶ 校验 ──▶ SQLite + 事件日志 ──▶ Obsidian 笔记
  GitHub Stars                                                          GitHub-Stars/
  Browser Bookmarks ──▶ 分类 ──▶ blocked? ─是─▶ _blocked JSONL          Browser-Bookmarks/<分类>/
  Single Web URL ──▶ SSRF 校验 ──▶ 提取(stdlib|crawl4ai|auto) ──▶ 分类    Web-Clips/<分类>/
```

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
