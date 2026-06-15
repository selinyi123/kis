# KIS HANDOFF（项目状态事实源）

> 本文件是 KIS 项目状态的唯一事实源（沿用 ClipVault 纪律）。每次切片完成后更新。

## 当前状态（2026-06-15）
- **阶段**：**v0.3.4 已交付** — 外部 Inbox 摄取（KIS-018）。**schema 不变（0.3.1）**，复用现有 KnowledgeCard。
- **v0.3.4 实测**：新增 `src/kis/ingest/`（safety/normalizer/dedupe/github_stars/bookmarks/web_clips/runner/report）+ `scripts/ingest_external.py` + 3 文档 + obsidian `render_external_inbox_md` + dashboard external_inbox 统计。三个低风险入口（github-stars/bookmarks/web-clips，**全无网络**，导入已导出文件）→ 安全(secret guard)→去重(normalized_url/content_hash/source_id)→ store(inbox)→ Obsidian `External-Inbox/`。**铁律：全部落 inbox(review=pending)，不自动 reviewed/canonical，不绕过 KIS-014；secret/blocked 不入库不入 Obsidian 仅进 report；不覆盖已有 canonical；dry-run 计数==real；幂等**。实测 fixtures：github seen4/created2/dup1/blocked1；bookmark seen5/created3/dup1/blocked1；web_clip seen5/created1/dup1/blocked1/errors2。dashboard External Inbox total=6 by source_type。**172/172 pytest 全绿**（+22；零网络/零 ResourceWarning）。`browser_bookmark` 复用既有 `web_bookmark`，不改 schema。报告写 `data/ingest_reports/`（gitignored）。
- **阶段（历史）**：v0.3.3 GBrain 只读试点（KIS-016/016R 判 B）；
- **v0.3.3 实测**：新增 `src/kis/gbrain_trial/`（config/filters/manifest/exporter/questions/baseline_search/adapters/runner/evaluator/report）+ `scripts/gbrain_trial.py`（export/questions/baseline/run/evaluate/report/all）+ 4 文档。三层隔离：vault→安全导出→快照→GBrain→仅报告。**铁律：GBrain 只读过滤快照不读原 vault；secret/blocked/DPMS 凭据(cookie/token/profile/qr/session)/.env/.db/.key 拒绝；不写回/不改 store/lifecycle/canonical；GBrain 非硬依赖，mock/manual 离线，subprocess 缺失优雅降级；输出仅 trial artifacts**。实测真实 vault：included=96 denied=0（vault 本就无敏感文件；过滤排除力由单测含 secret 的临时 vault 证明 denied≥6），citation_traceability=1.0 leakage=0 wrong_relation=0，decision keep_readonly/no writeback/no canonical。**148/148 pytest**（+35；零网络/零 LLM/零真实 GBrain/零 ResourceWarning）。
- **诚实说明**：mock 是 baseline 支撑→baseline_overlap=1.0、promote=yes 仅表示**框架+安全就绪**，非"GBrain 优于 baseline"真实结论；A/B/C 判断须等真实 GBrain（manual/subprocess）跑完。试点期修复 2 真实缺陷：泄漏检测改真实密钥模式（去 author→auth 假阳性）、二进制判定改只看 NUL（修中文 .md 误判）。
- **KIS-016R（真实 GBrain 质量验证）状态：装到导入为止，停在付费查询前**（2026-06-15，用户授权）。
  - 已装真实 GBrain：**Bun 1.3.14 + gbrain 0.42.44**（`~/.bun/bin/gbrain.exe`）；`init --pglite --no-embedding`（无 cron，脑库全局非 repo）；`import --no-embed` 导入 **96 页/262 chunks**（0 错）。真实 CLI：`import/query/search`（输出 `[score] slug -- snippet`）。
  - 已重写 `SubprocessGBrainAdapter`→真实 `gbrain query` + 解析器；`evaluator` 加 slug↔path 归一化；**150/150 pytest**。修复 import 在含空格路径 collect=0（用无空格暂存目录解决）。
  - **停在付费门槛**：embedding_model 默认 `zeroentropyai:zembed-1` 但无 key → embed/语义 query 不能跑。**待用户给嵌入 provider key**（ZEROENTROPY/OPENAI/VOYAGE 任一），我随后 `embed --all`→20 题 query→evaluate→report→出 A/B/C。
  - 仍未产出 A/B/C（无 key 不跑付费查询，不伪造）。KIS-016 keep_readonly 维持。manual 路径亦就绪（`manual-template`）。
- **KIS-016R 已完成（2026-06-15，Ollama-first 免费本地）→ 判 B**。装 Ollama 0.30.6 + nomic-embed-text(768d)；GBrain 原生支持 `ollama:` embedding（$0，无 key）。reinit-pglite 切 ollama + 手改 `~/.gbrain/config.json`(config set 写 DB 平面被 embed 管线忽略)→ embed --all 262chunks/96页 → 真实 gbrain query 跑 20 题。**结果：traceability 1.0 / missing 0.0 / leakage 0 / wrong_relation 0 / baseline_overlap 0.70 / usefulness 0.79 vs keyword baseline 0.79（持平）→ verdict=B（GBrain 安全可用但未跑赢免费关键词 baseline，保持 read-only，不进 KIS-017）**。store/obsidian/lifecycle 全未改。修 2 真实 harness bug（_norm 折叠分隔符、baseline_overlap 归一化）。150 pytest 全绿。环境：Bun+gbrain 在 ~/.bun，脑库 ~/.gbrain，Ollama+nomic 已装（可留作 KIS-017 复用）。**下一步非 KIS-017**：维持只读；再判 A 需更难问题集/更大语料/large·BGE-M3 对照（属 KIS-017）。
- **阶段（历史）**：v0.3.2 Dashboard；v0.3.1 Review Gate；v0.3.0 派生加工层。
- **v0.3.2 实测**：新增 `src/kis/dashboard/`（models/selectors/stats/commands/render）+ `scripts/build_review_dashboard.py`（`--dry-run/--only/--limit/--obsidian-dir/--db-path`）+ 2 文档。生成 7 页到 `<obsidian-dir>/Dashboards/`（总览/Inbox/Canonical Candidates/Archive Candidates/Deferred/Rejected/Stats）。**铁律：只读——不改 store/lifecycle/review；Inbox 页零 approve；canonical 候选只取 reviewed+(critical|hot)+(integrate|test)；建议命令仅复制不执行；dry-run 不写盘；build_pages 幂等；离线**。实测 cards=83 queue{inbox80/reviewed1/canonical1/archived1}；canonical_candidates=1，archive_candidates=31。**113/113 pytest 全绿**（+25：selectors/stats/render/cli/safety；零网络/零 LLM/零 ResourceWarning）。验收报告 docs/KIS-015_ACCEPTANCE.md。
- **阶段（历史）**：v0.3.1 Review Gate（KIS-014）；v0.3.0 派生加工层。
- **v0.3.1 实测**：schema 0.3.0→**0.3.1**（lifecycle.state 扩展 reviewed/canonical/rejected/deferred；新增可选 `review` 审计对象）。新增 `src/kis/review/`（policy/models/actions/queue/export）+ `scripts/review_cards.py` + 3 文档。**铁律：canonical 只能 reviewed→approve 显式人工产生；review 只写 lifecycle+review（assert_review_only 锁定 source/content/enrichment/linkage/safety/derived）；blocked 不入队；reason 非空；reviewer 默认 human；幂等 + 乐观版本锁；离线**。实测：inbox→reviewed→canonical 走通，archive 走通，**inbox→canonical 被拒**，export canonical OK。queue{inbox81/canonical1/archived1}。**88/88 pytest 全绿**（+27：policy/store/cli/obsidian/immutability；零网络/零 LLM/零 ResourceWarning）。验收报告见 docs/KIS-014_ACCEPTANCE.md。
- 设计说明：生命周期状态沿用 `lifecycle.state`（未新增 status 字段避免双状态不一致）；`review.previous_status/next_status` 记录迁移；`lifecycle.version` 作乐观锁。
- **阶段（历史）**：v0.3.0 AI 派生加工层。
- **v0.3.0 实测**：schema 0.2.2→**0.3.0**（新增可选 `derived` 层，含 generator 溯源 input_hash/prompt_hash/output_hash/model/generated_at）。新增 `src/kis/enrich/`（scoring/summary/project_relevance/prompt_contract/heuristic + providers/{base,mock,openai}）+ `scripts/enrich_cards.py` + `docs/KIS-013_PROMPT_INJECTION_BOUNDARY.md`。**铁律：derived 永不改 source/provenance（assert_only_derived 逐字段锁定）；blocked 不加工；heuristic 全离线；LLM 可选；LLM 不是事实源**。实测对 82 卡跑 heuristic：processed=82 updated=82 errors=0；value_level{hot37/warm28/cold14/critical3}；next_action{integrate34/archive26/test9/read5/ignore7/monitor1}。idempotent（重跑 skipped_done=82）。auto+mock 实测产 llm_generated。**61/61 pytest 全绿**（+18：heuristic9/schema3/provider4/cli2；零网络、零 LLM、零 ResourceWarning）。
- 注：blocked 卡片从不进 store（仅 _blocked JSONL），故 enrichment 的 skipped_blocked=0 是预期（无 blocked 卡可跳）。
- **阶段（历史）**：v0.2c Crawl4AI 可选后端；v0.2b 单 URL+SSRF；v0.2a 书签；v0.1 Stars。
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
