# GitHub Stars → Notion sync

Minimal adapter derived from [`brianlovin/github-stars-notion-sync`](https://github.com/brianlovin/github-stars-notion-sync) for the existing Notion database **GitHub 标星仓库**.

Target data source: `1c42c531-4691-4911-bccf-630a9366f744`.

## What it does

Every 10 minutes the Notion Worker reads GitHub `/user/starred` in `starred_at` descending order. It stores a `lastStarredAt` checkpoint and stops as soon as it reaches the previous checkpoint, so normal runs only inspect newly starred repositories.

For each new star it queries Notion by canonical GitHub URL first and `owner/repo` second. Existing rows are skipped; missing rows are created with:

- `名称` → `owner/repo`
- `Star 数` → current `stargazers_count`
- `介绍` → GitHub repository description
- `功能作用` → deterministic short description from repository description/topics; blank if evidence is insufficient
- `归属` → `本人` for `selinyi123`, otherwise `外部`
- `抓取日期` → current date in `Asia/Taipei`
- `链接` → canonical GitHub repository URL

No LLM is involved in routine synchronization.

## Reliability rules

- No full Notion scan during normal runs.
- No duplicate creation when URL or name already exists.
- If any repository fails during a delta cycle, the checkpoint is **not advanced**. The next run retries safely instead of silently losing that star.
- First deployment performs a one-time walk from the newest star backwards; existing Notion rows are skipped by exact lookup.

## Setup

Prerequisites: Node.js 22+, npm 10.9.2+, and the Notion `ntn` CLI authenticated to the workspace.

```bash
cd tools/github-stars-notion-sync
npm install
npm run setup
```

`npm run setup` will:

1. verify access to the existing Notion data source;
2. ask for a Notion Personal Access Token with Notion API + Workers access;
3. show the exact GitHub OAuth App settings and ask for its Client ID / Client Secret;
4. create the Notion Worker if needed;
5. deploy the Worker and push environment variables;
6. open GitHub OAuth authorization using read-only `read:user` scope;
7. trigger the initial synchronization.

GitHub OAuth callback URL:

```text
https://www.notion.so/workers/oauth/callback
```

Secrets are stored only in the local `.env`, which is ignored by Git.

## Validation

```bash
npm test
npm run check
```

The repository PR also includes a path-scoped GitHub Actions check for this adapter.

## Upstream

The incremental sync/OAuth pattern is adapted from `brianlovin/github-stars-notion-sync` under the MIT License. See `LICENSE` and `NOTICE.md`.
