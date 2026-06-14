# KIS HANDOFF（项目状态事实源）

> 本文件是 KIS 项目状态的唯一事实源（沿用 ClipVault 纪律）。每次切片完成后更新。

## 当前状态（2026-06-14）
- **阶段**：**v0.2c 已交付** — 单 URL 剪藏新增可选提取后端（Crawl4AI），stdlib 仍为默认基线。
- **v0.2c 实测**：schema 0.2.1→**0.2.2**（source.extraction_engine/extraction_status/extraction_error；content.clean_markdown/structured_data）。新增 `src/kis/extractors/`（base/stdlib_html/crawl4ai_adapter）。`ingest_url.py --extractor stdlib|crawl4ai|auto`（默认 stdlib）。实测：stdlib→success；auto（crawl4ai 未装）→**fallback** 降级 stdlib；crawl4ai 强制→**failed 明确报错不伪装**。Crawl4AI 延迟导入、非硬依赖（`crawl4ai installed: False` 下全流程正常）。**43/43 pytest 全绿**（+13：4 extractors + 9 crawl4ai adapter；零网络、零浏览器、零 ResourceWarning）。库仍 38+39+5=82 卡。
- **阶段（历史）**：v0.2b 单 URL 剪藏 + SSRF 防线；v0.2a 浏览器书签；v0.1 GitHub Stars。
- **v0.2b 实测**：schema 演进 0.2.0→**0.2.1**（content 增 description/text_preview；source 增 site_name/http_status/fetched_at/fetch_error）。`ingest_url.py` 实测处理 5 类 URL（example/GitHub/HuggingFace/Python博客/Tripo3D）全部 inserted，分类正确（HF→ai_workspace, Tripo→visual_tools, MemOS→agent_tools）。SSRF 防线：file/ftp/javascript/data/about scheme + localhost + 私网/环回/链路本地 IP（含 169.254.169.254）全部拦截。**30/30 pytest 全绿**（含 10 个 web_url，零网络依赖、零 ResourceWarning）。修复 classify 短子串误判（"rom"误配"from" 等）。当前库：github_star 38 + web_bookmark 39 + web_clip 5 = 82 卡。
- **阶段（历史）**：v0.2a 浏览器书签接入；v0.1 GitHub Stars 闭环。
- **v0.2a 实测**：schema 演进到 **0.2.0**（新增 source_type / source_id / normalized_url / folder_path / authority / sensitivity）。`ingest_bookmarks.py` 实测导入 `bookmarks_2026_6_14.html`：parsed=42, inserted=39, **blocked=3**（免税地址/反检测浏览器/机场，写入 _blocked JSONL，未入库未入 Obsidian）, invalid=0。GitHub Stars 同步重建 38 卡。**20/20 pytest 全绿**（12 pipeline + 8 bookmarks）。
- **KIS-007 验收**：8 条标准全部满足（导入成功 / 39≥30 有效卡 / 3 类敏感书签拦截 / 每卡含 source_url+source_id+content_hash+captured_at+sensitivity+authority+status / SQLite 可按 source_type=web_bookmark 查询 / Obsidian 按分类目录浏览 / 测试通过 / 本 HANDOFF 更新）。
- **Obsidian**：`KIS 知识情报系统\Browser-Bookmarks\{AI-Workspace,Agent-Tools,Visual-Tools,Dev-Resources,Research,Trading-Research,Ops-Internal,General}` 共 39 卡已上传。
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
