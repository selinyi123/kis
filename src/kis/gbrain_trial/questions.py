"""The 20 real trial questions (KIS-016). Cross-project, lifecycle, boundaries."""

from __future__ import annotations

import json
import os
from typing import Any


def _q(qid, question, expected_sources, expected_claims, risk_tags):
    return {"id": qid, "question": question, "expected_sources": expected_sources,
            "expected_claims": expected_claims, "risk_tags": risk_tags}


QUESTIONS: list[dict[str, Any]] = [
    _q("q001", "ClipVault 当前定位是什么？", ["ClipVault"], ["采集", "剪切板"], ["cross_project"]),
    _q("q002", "ClipVault 为什么不能被 GBrain/MemOS 替代？", ["ClipVault", "架构"], ["事实源", "派生"], ["cross_project", "sensitive_boundary"]),
    _q("q003", "Prompt Performance Engine 在记忆系统中是什么角色？", ["Prompt", "架构"], ["证据", "评测"], ["cross_project"]),
    _q("q004", "DPMS 哪些数据不能进入通用记忆？", ["DPMS"], ["cookie", "令牌", "凭据"], ["sensitive_boundary"]),
    _q("q005", "DPMS 可以导入通用记忆的脱敏内容有哪些？", ["DPMS"], ["脱敏", "公开设计"], ["sensitive_boundary"]),
    _q("q006", "KIS 当前生命周期状态有哪些？", ["路线", "架构", "HANDOFF"], ["inbox", "canonical"], ["lifecycle"]),
    _q("q007", "canonical 为什么必须人工产生？", ["路线", "HANDOFF"], ["人工", "闸门"], ["lifecycle"]),
    _q("q008", "derived 为什么不能作为事实源？", ["架构", "HANDOFF"], ["建议", "事实源"], ["lifecycle"]),
    _q("q009", "GitHub Stars 中哪些项目属于记忆/知识库核心？", ["GitHub-Stars", "MemOS", "codegraph"], ["MemOS", "记忆"], ["cross_project"]),
    _q("q010", "GBrain 与 MemOS 的阶段区别是什么？", ["路线"], ["只读", "记忆"], ["cross_project"]),
    _q("q011", "为什么 Obsidian 是权威事实层？", ["架构"], ["权威", "事实"], ["sensitive_boundary"]),
    _q("q012", "Review Dashboard 为什么不能提供 inbox approve？", ["路线", "架构"], ["人工", "canonical"], ["lifecycle"]),
    _q("q013", "哪些内容必须人工确认后才能进入 canonical？", ["HANDOFF", "路线"], ["reviewed", "人工"], ["lifecycle"]),
    _q("q014", "当前外部数据入口的风险是什么？", ["架构", "报告"], ["合规", "注入"], ["sensitive_boundary"]),
    _q("q015", "Crawl4AI 在架构里适合做什么？", ["报告", "架构"], ["markdown", "提取"], ["cross_project"]),
    _q("q016", "MediaCrawler 为什么必须合规低频隔离？", ["报告"], ["合规", "隔离"], ["sensitive_boundary"]),
    _q("q017", "Agent-Reach 适合放在哪一层？", ["报告"], ["连接器", "采集"], ["cross_project"]),
    _q("q018", "Prompt Engine 如何评测记忆系统？", ["Prompt"], ["评测", "证据"], ["cross_project"]),
    _q("q019", "哪些资料永远不能进入通用记忆？", ["架构", "DPMS"], ["凭据", "敏感"], ["sensitive_boundary"]),
    _q("q020", "当前系统下一阶段是否应该接 MemOS？为什么？", ["路线", "HANDOFF"], ["先", "审阅"], ["cross_project", "stale_data"]),
]


def write_questions(out_dir: str) -> str:
    path = os.path.join(out_dir, "questions", "questions.jsonl")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        for q in QUESTIONS:
            fh.write(json.dumps(q, ensure_ascii=False) + "\n")
    return path
