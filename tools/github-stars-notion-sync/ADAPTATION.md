## Design

- Reuse the incremental `starred_at` checkpoint model from `brianlovin/github-stars-notion-sync`.
- Do not full-scan the Notion database on each run.
- Stop fetching GitHub stars once `starred_at <= lastStarredAt`.
- Upsert by canonical GitHub URL first, then `owner/repo` name.
- Write only into the existing Notion data source.
- No LLM is required for normal synchronization.

## Existing Notion property mapping

- `名称` ← `owner/repo`
- `Star 数` ← `stargazers_count`
- `介绍` ← repository `description`
- `功能作用` ← concise deterministic summary from description/topics; leave blank when insufficient
- `归属` ← `本人` when owner is `selinyi123`, otherwise `外部`
- `抓取日期` ← sync date in Asia/Taipei
- `链接` ← canonical repository URL
