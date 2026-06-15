# KIS-016 — Sensitive Filter Policy（安全导出策略）

GBrain **只读经过过滤的快照**，绝不直接读原始 vault。导出偏向**排除**：误排一张卡无害，
泄漏一个凭据有害。

## 三层隔离
```
Obsidian Vault → KIS Safe Export Filter → .kis/gbrain_trial/exported_vault/ → GBrain → 仅报告
```

## 允许（allowlist 目录 + 根级笔记）
`Dashboards/ · GitHub-Stars/ · Browser-Bookmarks/ · Web-Clips/ · ClipVault Personal/ ·
Prompt Performance Engine/ · DPMS-Platform/（仅脱敏/公开设计文档）` + vault 根级 `.md` 笔记。

## 拒绝
- **路径含敏感 token**（子串匹配，小写）：`blocked secret confidential private token cookie
  credential profile qr session proxy password otp auth key .env`
- **扩展名**：`.db .sqlite .sqlite3 .env .key .pem .p12 .pfx .jsonl .exe .dll .bin .zip
  .png .jpg .jpeg .gif .pdf`
- `.json` 默认拒绝（除非显式 allowlist）
- 非 allowlist 目录
- 体积 > 1MB（视为原始导出）
- 含 NUL 字节的二进制文件

## 二级保险
- **导出阶段**仅按路径/扩展/体积/NUL 过滤（不读内容做正则）。
- **评估阶段**额外做泄漏审计：引用若落在导出之外或路径含敏感 token，或答案含真实密钥模式
  （`sk-…`/`AKIA…`/`ghp_…`/`BEGIN PRIVATE KEY`/长 hex）→ 计为 leakage。
- 词汇级（"auth"⊂"author"、"key"⊂"API key"）**不计**泄漏，避免假阳性。

## DPMS 边界
DPMS 的 cookie/token/profile/qr/session/admin/proxy 文件**永不导出**；仅"脱敏复盘 / 公开设计文档"可入。
