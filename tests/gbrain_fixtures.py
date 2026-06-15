"""Shared fixtures for KIS-016 GBrain trial tests (a temp vault + export)."""

import os

_ALLOWED = {
    "01 架构.md": "# 架构\nObsidian 是权威事实层。ClipVault 写入 Obsidian。derived 是建议不是事实源。",
    "03 路线图.md": "# 路线图\nKIS 生命周期 inbox reviewed canonical archived。canonical 必须人工产生。先审阅再接 MemOS。",
    "GitHub-Stars/MemTensor-MemOS.md": "# MemTensor/MemOS\nmemory OS for agents, RAG, ClipVault Obsidian 记忆 知识库核心。",
    "Web-Clips/General/Example.md": "# Example\nA web clip about crawler and search.",
    "Browser-Bookmarks/Ops-Internal/router.md": "# router\ninternal ops note.",
    "DPMS-Platform/脱敏复盘.md": "# 脱敏复盘\nDPMS 公开设计文档，脱敏内容可入通用记忆。",
}
_DENIED = {
    "_blocked/blocked-bookmarks.jsonl": '{"url":"x"}',
    "secret/token.md": "secret token here",
    "browser-profile/qr-session.md": "qr session cookie",
    "DPMS-Platform/cookie-token.md": "cookie token admin",
    "creds/credential.txt": "password otp",
    "data.db": "rawsqlite",
    "app/.env": "OPENAI_API_KEY=sk-xxx",
}


def make_vault(root: str) -> str:
    vault = os.path.join(root, "vault")
    for rel, body in {**_ALLOWED, **_DENIED}.items():
        p = os.path.join(vault, *rel.split("/"))
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "w", encoding="utf-8") as fh:
            fh.write(body)
    return vault


def allowed_count() -> int:
    return len(_ALLOWED)
