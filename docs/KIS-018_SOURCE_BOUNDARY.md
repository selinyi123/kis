# KIS-018 — Source Boundary（外部摄取边界）

外部资料只能经**安全、可审计**的通道进入 inbox，绝不直接成为事实。

## 本阶段三个低风险入口（均无网络，导入已导出的文件）
| CLI | 输入 | source_type |
|---|---|---|
| `github-stars` | `*.json` / `*.md`（GitHub Stars 快照） | `github_star` |
| `bookmarks` | `*.html`（Chrome/Edge/Firefox 书签导出） | `web_bookmark`（≡ 任务书的 browser_bookmark） |
| `web-clips` | `*.jsonl`（手动/clipper 导出的标题+正文） | `web_clip` |

## 不可逾越（任务书 12 条）
1. 不自动 canonical 2. 不自动 reviewed 3. 不绕过 KIS-014 Review Queue
4. 不写 blocked/secret 内容 5. 不抓登录墙私人内容 6. 不抓未授权聊天/邮件/账号
7. 不接 DPMS 敏感事件 8. 不存 Cookie/Token/私钥/OTP/浏览器 profile
9. 不做无边界社媒抓取 10. 不让外部来源覆盖已有 card（dedupe + 不动已有 canonical）
11. 每条必带 source_url/source_id/content_hash/captured_at 12. 全程 dry-run 可预览

## Secret Guard（拦截即不入库）
命中以下任一 → **blocked**（不入 store、不入 Obsidian，仅进 report）：
`sk-… · ghp_… · AKIA… · BEGIN PRIVATE KEY · password= · token= · cookie= · session= · otp · .env`
此外，书签分类判定为 `sensitivity=blocked`（成人/机场/免税地址/反检测）也一并 blocked。

## Dedupe（三键）
`normalized_url` · `content_hash` · `(source_type, source_id)`。再导入同一条 → `skipped_duplicate`；
dry-run 与真实导入计数一致（去重只读 store）。

## 生命周期
所有新卡 `lifecycle.state = inbox`，`review = pending`。升级 reviewed/canonical 只能走 KIS-014 人工命令。

## 不做（留后续）
Crawl4AI 显式 URL 抓取 → KIS-019；硬语义 benchmark → KIS-020；provider 对比 → KIS-021。
