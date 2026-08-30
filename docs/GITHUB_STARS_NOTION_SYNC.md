# GitHub Stars → Notion 增量同步

KIS 直接把 GitHub Stars 增量写入现有 Notion 数据库，不新增第二套收藏库，也不依赖 LLM、Zapier、Notion Workers 或常驻服务器。

## 运行模型

稳态每次调度只做两件事：

1. 从 Notion 读取最新的 `标星时间`，作为持久化水位线。
2. 从 GitHub 按 `starred_at` 倒序读取 Stars，遇到早于水位线的记录立即停止。

只有水位线之后的仓库才会进入写入路径。新仓库按最老 → 最新顺序写入，因此中途失败不会让水位线越过失败项；下一次运行会安全重试。

第一次运行没有水位线时，会读取现有 Notion 行并寻找最近一个已经存在的 GitHub Star，以此建立边界；不会无条件重新导入全部历史 Stars。

## Notion 字段映射

目标 Data Source：`1c42c531-4691-4911-bccf-630a9366f744`

- `名称` → `owner/repo`
- `Star 数` → GitHub `stargazers_count`
- `介绍` → GitHub repository description
- `功能作用` → description；description 为空时才读取 README，并做确定性短摘要，不调用 LLM
- `归属` → owner 为 `selinyi123` 时为 `本人`，否则为 `外部`
- `抓取日期` → Asia/Taipei 当日日期
- `链接` → canonical GitHub URL
- `标星时间` → GitHub `starred_at`，同时作为增量水位线

## 一次性配置

GitHub Actions 需要一个仓库 Secret：

`NOTION_API_TOKEN`

它必须是有权访问“GitHub 标星仓库”数据库的 Notion API token。不要把 token 写进代码、Issue、日志或 `.env` 后提交。

在 GitHub 仓库中进入：

`Settings → Secrets and variables → Actions → New repository secret`

Name 填 `NOTION_API_TOKEN`，Value 填 Notion token。

未配置 Secret 时，工作流会安全退出并返回成功，不会产生失败噪音或任何写入。

## 调度

`.github/workflows/sync-github-stars-to-notion.yml` 每小时第 17、47 分钟运行，即约每 30 分钟一次；也支持 `workflow_dispatch` 手动触发。

## 本地运行

PowerShell：

```powershell
$env:NOTION_API_TOKEN="<token>"
python scripts/sync_github_stars_to_notion.py
```

可选环境变量：

- `GITHUB_USERNAME`，默认 `selinyi123`
- `NOTION_DATA_SOURCE_ID`，默认现有目标数据库
- `GITHUB_TOKEN`，可选；GitHub Actions 会自动提供

## 设计约束

- 零运行时第三方 Python 依赖，只使用标准库。
- 不扫描 Notion 全库作为日常去重手段；全库读取只允许发生在首次建立水位线时。
- 不使用 LLM 生成同步数据，避免 token 成本和非确定性。
- URL 优先、名称兜底去重；重新 Star 同一仓库不会创建重复行。
- 同秒多个 Star 通过“等于水位线仍允许重放 + Notion 幂等检查”避免漏项。
