# KIS HANDOFF（项目状态事实源）

> 本文件是 KIS 项目状态的唯一事实源（沿用 ClipVault 纪律）。每次切片完成后更新。

## 当前状态（2026-06-14）
- **阶段**：v0.1 最小可运行闭环 **已交付**。
- **底座决策**：新建独立 `kis` 仓库（用户拍板，2026-06-14）。
- **GitHub**：已建私有仓库 **https://github.com/selinyi123/kis**（PRIVATE，默认分支 main），v0.1 已首推（16 文件，commit ff6e90f）。本地 main 跟踪 origin/main。git 身份 local 设为 selinyi123 / 邮箱。
- **Obsidian**：已上传到库 `D:\TOOL\OBSIDIAN\Home\prompt仓库\KIS 知识情报系统\`（主页 + 报告 + 5 文档 + 37 张标星卡片）。
- **v0.1 范围决策**：三源闭环架构，但 v0.1 先交付 GitHub Stars 单源贯通链路（用户拍板）。

## 已验证事实
- 单元测试：`python -m unittest discover -s tests -v` → **11/11 green**（身份/schema/幂等/搜索/Obsidian）。
- 实测：`python scripts/ingest_github_stars.py` → 拉取 **37 个 star**，run1 inserted=37，run2 unchanged=37（**幂等无重复**）。
- FTS5：可用（`fts_enabled=True`），`search('memory OR knowledge')` 命中 MemOS/codegraph/crawl4ai 等。
- 项目关联：规则命中正常（如 MemOS → [KIS, prompt-performance-engine]）。
- Obsidian：37 篇笔记输出到 `vault_out/github_stars/`，frontmatter + topics 标签 + wikilink 正确。

## 关键决策记录
- D-001：身份 `id=kc_<16hex(sha256(connector|url))>` 主键；`content_hash=sha256(title+body)` 做变更检测。
- D-002：零第三方运行时依赖 → 手写最小 JSON-Schema 校验器（拒绝未知字段）。
- D-003：enrichment 字段在 v0.1 用确定性默认值占位（value_score=0/cold/heuristic），v0.2 接 LLM 不破坏 schema。
- D-004：存储先 SQLite+FTS5，v0.3 迁 MemOS（schema 兼容）。
- D-005：Obsidian 默认导出到本地 `vault_out/`（gitignored），需显式 `--obsidian-out` 才写真实库。

## 环境
- Python 3.11.9，无第三方依赖。gh CLI 已登录 `selinyi123`（keyring，repo scope）。
- gh 路径：脚本自动探测 PATH 或 `C:\Program Files\GitHub CLI\gh.exe`。

## 下一步（待用户指令）
1. ~~建私有 `kis` repo 并首推~~ ✅ 已完成（2026-06-14）。
2. v0.2 开工：KIS-007 网页连接器 / KIS-008 剪切板源 / KIS-009 标签体系 / KIS-013 价值评分。
3. 把 `ingest_github_stars.py` 抽象为 `BaseConnector` 子类（KIS-003）。
4. 用 LLM 真正加工 37 张标星卡片的 summary/value_level（当前确定性占位 cold/heuristic）。

## 角色纪律
Architect（Claude）写切片规格并裁决验收；用户最终拍板。每切片：实现 → 纯函数单测 → 更新本 HANDOFF → （授权后）push → Obsidian 同步。
