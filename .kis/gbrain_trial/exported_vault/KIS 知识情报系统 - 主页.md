---
title: KIS 知识情报系统
type: project-home
status: v0.1 闭环已交付
created: 2026-06-14
tags: [KIS, 知识库, 知识情报, 多源采集, project]
related: ["[[ClipVault Personal]]", "[[DPMS-Platform]]", "[[Prompt Performance Engine]]"]
---

# 🧠 KIS — 多源个人知识情报系统

把分散在 **GitHub Stars / 剪切板 / 网页 / X / 知乎 / B站 / 小红书 / 本地文档** 的信息流，沉淀为**可搜索、可同步、可被 AI/Codex 调用**的结构化知识资产。

> 不是更大的收藏夹，而是一个**知识运行时引擎**：采集 → 清洗 → 去重 → 摘要 → 分类 → 打标 → 价值评分 → 主题聚类 → 项目关联 → 更新跟踪 → 同步归档。

## 架构等式
`KIS = ClipVault 采集底座 + DPMS 管道/评分内核 + PPE 证据纪律 + MemOS 记忆运行时`
复用三个已有项目的**模式**：[[ClipVault Personal]]（采集/同步/安全）、[[DPMS-Platform]]（管道/评分/事件源）、[[Prompt Performance Engine]]（证据契约纪律）。

## 当前状态：v0.1 最小可运行闭环 ✅
已跑通 **GitHub Stars → KnowledgeCard → SQLite(FTS5) → Obsidian Note**，幂等、可搜索、自动项目关联。
- 11/11 单元测试全绿
- 实测拉取 **37 个 star**，重跑零重复（幂等）
- 本文件夹「GitHub Stars 卡片」即首批 37 张知识卡片产物

## 文档导航
- [[01 调研报告与落地蓝图]] — bil/dpms 仓库审阅 + 标星分析 + 系统蓝图（完整）
- [[02 架构]] — 分层架构与模块
- [[03 路线图]] — v0.1→v2.0 + 任务包 P0/P1/P2
- [[04 开发日志 HANDOFF]] — 状态事实源
- [[05 产品规格]] — 使命/源/生命周期/验收

## 标星映射（核心节点 → 替代方案）
| 系统节点 | 主选 | 卡片 |
|---|---|---|
| 多源连接器 | Agent-Reach + MediaCrawler | [[Panniantong-Agent-Reach]] · [[NanmiCoder-MediaCrawler]] |
| 网页清洗 | crawl4ai | [[unclecode-crawl4ai]] |
| 记忆/检索 | MemOS | [[MemTensor-MemOS]] |
| 服务 Codex | codegraph | [[colbymchenry-codegraph]] |
| 知识图谱 | Understand-Anything | [[Egonex-AI-Understand-Anything]] |
| 研究报告 | last30days-skill | [[mvanhorn-last30days-skill]] |

## 本地工程位置
`D:\AI\CLAUDE CODE\Work Program\KIS\`（源码 + schema + 连接器脚本 + 测试）。尚未在 GitHub 建 repo（待授权首推）。

## 下一步
- P0 剩余：建 GitHub 私有 `kis` repo 首推
- v0.2：网页连接器(crawl4ai) → 剪切板源(对接 ClipVault) → 标签体系 → 价值评分 → BaseConnector 抽象
