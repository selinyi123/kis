# KIS-016 — Trial Questions（20 个真实问题）

覆盖跨项目、跨项目关系、生命周期、敏感边界。结构化版本见
`.kis/gbrain_trial/questions/questions.jsonl`（每条含 id/question/expected_sources/
expected_claims/risk_tags）。

| id | 问题 | risk tags |
|---|---|---|
| q001 | ClipVault 当前定位是什么？ | cross_project |
| q002 | ClipVault 为什么不能被 GBrain/MemOS 替代？ | cross_project, sensitive_boundary |
| q003 | Prompt Performance Engine 在记忆系统中是什么角色？ | cross_project |
| q004 | DPMS 哪些数据不能进入通用记忆？ | sensitive_boundary |
| q005 | DPMS 可以导入通用记忆的脱敏内容有哪些？ | sensitive_boundary |
| q006 | KIS 当前生命周期状态有哪些？ | lifecycle |
| q007 | canonical 为什么必须人工产生？ | lifecycle |
| q008 | derived 为什么不能作为事实源？ | lifecycle |
| q009 | GitHub Stars 中哪些项目属于记忆/知识库核心？ | cross_project |
| q010 | GBrain 与 MemOS 的阶段区别是什么？ | cross_project |
| q011 | 为什么 Obsidian 是权威事实层？ | sensitive_boundary |
| q012 | Review Dashboard 为什么不能提供 inbox approve？ | lifecycle |
| q013 | 哪些内容必须人工确认后才能进入 canonical？ | lifecycle |
| q014 | 当前外部数据入口的风险是什么？ | sensitive_boundary |
| q015 | Crawl4AI 在架构里适合做什么？ | cross_project |
| q016 | MediaCrawler 为什么必须合规低频隔离？ | sensitive_boundary |
| q017 | Agent-Reach 适合放在哪一层？ | cross_project |
| q018 | Prompt Engine 如何评测记忆系统？ | cross_project |
| q019 | 哪些资料永远不能进入通用记忆？ | sensitive_boundary |
| q020 | 当前系统下一阶段是否应该接 MemOS？为什么？ | cross_project, stale_data |
