"""Deterministic bookmark classification (KIS-007).

Rule-based, no LLM. Each bookmark is matched (case-insensitive) against a
haystack of title + url + folder_path. Rules are evaluated in priority order so
the most safety-relevant verdict wins:

    blocked  ->  trading_research  ->  ops_tools  ->  ai_workspace
             ->  agent_tools  ->  visual_tools  ->  dev_resources
             ->  research  ->  general (fallback)

Verdicts (the ``decision`` field) drive ingest:
  * ``blocked``  : NOT written to Obsidian or SQLite; appended to a blocked log.
  * ``isolate``  : written, but routed to an isolated folder (trading research).
  * ``ingest``   : written normally.

This is the privacy boundary: detection-evasion, proxy "airport", tax-free
address, and adult bookmarks never enter the knowledge memory.
"""

from __future__ import annotations

# (category, decision, sensitivity, obsidian_folder, keywords)
_RULES: list[tuple[str, str, str, str, tuple[str, ...]]] = [
    ("blocked", "blocked", "blocked", "", (
        "成人", "porn", "xxx", "sex", "av在线", "色情",
        "机场", "proxy airport", "节点订阅", "代理凭据", "梯子",
        "免税", "tax-free", "taxfree", "usaddressgen", "地址生成", "address generator",
        "反检测", "antidetect", "mostlogin", "多账号运营", "指纹浏览器",
    )),
    ("trading_research", "isolate", "internal", "Trading-Research", (
        "quant", "polymarket", "trading", "量化", "交易", "easyquant", "预测市场",
    )),
    # NOTE: keywords are substring-matched, so short generic tokens like bare
    # "ip"/"rom"/"hive"/"paper" are avoided — they false-match from/archive/
    # wallpaper. Prefer specific multi-char tokens.
    ("ops_tools", "ingest", "internal", "Ops-Internal", (
        "vpn", "webvpn", "刷机", "刷机包", "rom乐园", "rom下载", "romleyuan",
        "路由", "软路由", "router", "ip查询", "ip 查询", "ip分流", "koolcenter", "net.coffee",
    )),
    ("ai_workspace", "ingest", "public", "AI-Workspace", (
        "chatgpt", "openai", "gemini", "ai studio", "aistudio", "hugging face",
        "huggingface", "claude", "z.ai", "zhipu", "智谱", "kimi", "通义", "文心",
    )),
    ("agent_tools", "ingest", "public", "Agent-Tools", (
        "agent", "perplexity", "skillhub", "accio", "dify", "hivehq", "蜂巢",
    )),
    ("visual_tools", "ingest", "public", "Visual-Tools", (
        "image", "3d", "tripo", "hyper3d", "rodin", "midjourney", "绘画", "gallery", "gpt-image",
    )),
    ("dev_resources", "ingest", "public", "Dev-Resources", (
        "github", "博客园", "scriptcat", "deepl", "gitee", "stackoverflow", "掘金", "csdn",
    )),
    ("research", "ingest", "public", "Research", (
        "oalib", "open access", "论文", "arxiv", "scholar", "搜索", "资料", "metaso", "秘塔",
    )),
]

_FALLBACK = ("general", "ingest", "public", "General")


def classify_bookmark(title: str, url: str, folder_path: str = "") -> dict[str, str]:
    """Return {category, decision, sensitivity, folder} for a bookmark."""
    haystack = f"{title} {url} {folder_path}".lower()
    for category, decision, sensitivity, folder, keywords in _RULES:
        if any(k in haystack for k in keywords):
            return {"category": category, "decision": decision, "sensitivity": sensitivity, "folder": folder}
    category, decision, sensitivity, folder = _FALLBACK
    return {"category": category, "decision": decision, "sensitivity": sensitivity, "folder": folder}
