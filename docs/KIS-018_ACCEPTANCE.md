# KIS-018 — Acceptance Report

```
KIS-018 completed
tests: 172/172 green (22 new: github_stars/bookmarks/web_clips/safety/dedupe/cli/report/obsidian/dashboard/immutability)
sources_enabled: github_stars / browser_bookmarks(web_bookmark) / web_clips
cards_seen: 14 (4 + 5 + 5 across fixtures)
cards_created: 6 (2 + 3 + 1)
skipped_duplicate: 3 (1 + 1 + 1)
blocked: 3 (token=ghp_ / 机场 sensitivity / sk- secret)
errors: 2 (web_clip: missing url + malformed line)
dry_run: pass (counts identical to real)
dedupe: pass (normalized_url / content_hash / source_id)
secret_guard: pass (sk-/ghp_/PRIVATE KEY/.env/...)
default_inbox: pass (all new cards lifecycle.state=inbox)
no_auto_reviewed: pass
no_auto_canonical: pass
obsidian_external_inbox: pass (External-Inbox/{GitHub-Stars,Browser-Bookmarks,Web-Clips})
dashboard_updated: pass (external_inbox total=6 by source_type)
```

## 对照交付标准
| 标准 | 结果 |
|---|---|
| 三个低风险入口完成 | ✅ github-stars / bookmarks / web-clips |
| 所有新卡默认 inbox | ✅ states == {inbox}，review=pending |
| 无任何自动 canonical / reviewed | ✅ 测试断言 |
| blocked 不入库、不入 Obsidian | ✅ 仅进 report；store/External-Inbox 不含 |
| 重复导入幂等 | ✅ 二次真实导入 created=0、skipped_duplicate≥2 |
| dry-run 可用且计数一致 | ✅ dry == real |
| 不修改已有 canonical card | ✅ 预置 canonical MemOS，导入后仍 canonical |
| dashboard 更新 | ✅ External Inbox by source_type / by project + Last Ingest Run |
| docs/HANDOFF/ROADMAP/README 更新 | ✅ |

## 设计说明
- 复用现有 schema（0.3.1），`browser_bookmark` 映射到既有 `web_bookmark`，不新增重复 source_type。
- 复用 `card.py` 构建器、`classify`、`store.upsert`、`obsidian` —— 外部卡片与全系统同一 KnowledgeCard。
- 全程无网络（导入已导出文件）；Crawl4AI 显式抓取留 KIS-019。

## 边界确认（未做，符合要求）
未做：网络抓取 / 登录墙私人内容 / DPMS 敏感事件 / Cookie·Token·私钥存储 / 无边界社媒抓取 / 自动 canonical。
