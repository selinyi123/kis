import { Worker } from "@notionhq/workers";
import * as Builder from "@notionhq/workers/builder";
import * as Schema from "@notionhq/workers/schema";

import { CONFIG } from "./config.js";
import { getStarredPage } from "./github.js";
import { createNotionClient, ensureRepoRow } from "./notion.js";

const NOTION_API_TOKEN = process.env.NOTION_API_TOKEN ?? "";
const GITHUB_CLIENT_ID = process.env.GITHUB_CLIENT_ID ?? "";
const GITHUB_CLIENT_SECRET = process.env.GITHUB_CLIENT_SECRET ?? "";

function assertEnv() {
  const missing = [
    ["NOTION_API_TOKEN", NOTION_API_TOKEN],
    ["GITHUB_CLIENT_ID", GITHUB_CLIENT_ID],
    ["GITHUB_CLIENT_SECRET", GITHUB_CLIENT_SECRET],
  ].filter(([, value]) => !value).map(([name]) => name);
  if (missing.length) throw new Error(`Missing env: ${missing.join(", ")}`);
}

const worker = new Worker();
export default worker;

const runStatus = [
  { name: "Success", color: "green" as const },
  { name: "Partial", color: "yellow" as const },
  { name: "Failed", color: "red" as const },
];

const syncRuns = worker.database("syncRuns", {
  type: "managed",
  initialTitle: "GitHub Stars sync runs",
  primaryKeyProperty: "Run ID",
  schema: {
    properties: {
      "Run ID": Schema.title(),
      Started: Schema.date(),
      Status: Schema.select(runStatus),
      Created: Schema.number(),
      Existing: Schema.number(),
      Errors: Schema.number(),
    },
  },
});

const githubAuth = worker.oauth("githubAuth", {
  name: "github-oauth",
  authorizationEndpoint: "https://github.com/login/oauth/authorize",
  tokenEndpoint: "https://github.com/login/oauth/access_token",
  scope: "read:user",
  clientId: GITHUB_CLIENT_ID,
  clientSecret: GITHUB_CLIENT_SECRET,
});

interface DeltaState {
  lastStarredAt?: string;
  page?: number;
  cycleNewest?: string;
  cycleHadError?: boolean;
}

worker.sync("githubStarsDelta", {
  database: syncRuns,
  mode: "incremental",
  schedule: "10m",
  execute: async (rawState: DeltaState | undefined) => {
    assertEnv();
    const started = new Date();
    const token = await githubAuth.accessToken();
    const notion = createNotionClient(NOTION_API_TOKEN);
    const state = rawState ?? {};

    const baseline = state.lastStarredAt ?? "";
    const page = state.page ?? 1;
    let cycleNewest = state.cycleNewest ?? baseline;
    let cycleHadError = state.cycleHadError ?? false;

    const result = await getStarredPage(token, page, CONFIG.perPage);
    let created = 0;
    let existing = 0;
    const errors: string[] = [];
    let stopped = false;

    for (const star of result.items) {
      if (baseline && star.starredAt <= baseline) {
        stopped = true;
        break;
      }
      if (!cycleNewest || star.starredAt > cycleNewest) cycleNewest = star.starredAt;

      try {
        const outcome = await ensureRepoRow(notion, CONFIG.dataSourceId, star);
        if (outcome === "created") created++;
        else existing++;
      } catch (error) {
        cycleHadError = true;
        errors.push(`${star.fullName}: ${error instanceof Error ? error.message : String(error)}`);
      }
    }

    const moreToFetch = !stopped && result.hasNextPage && result.items.length > 0;
    const finalState: DeltaState | undefined = moreToFetch
      ? {
          lastStarredAt: baseline || undefined,
          page: page + 1,
          cycleNewest: cycleNewest || undefined,
          cycleHadError,
        }
      : cycleHadError
        ? (baseline ? { lastStarredAt: baseline } : undefined)
        : (cycleNewest ? { lastStarredAt: cycleNewest } : undefined);

    const status: "Success" | "Partial" | "Failed" = errors.length === 0
      ? "Success"
      : created + existing > 0 ? "Partial" : "Failed";
    const runId = `run-${started.toISOString().replace(/[:.]/g, "-")}-p${page}`;

    if (errors.length) console.error(errors.join("\n"));
    console.log(`page=${page} created=${created} existing=${existing} errors=${errors.length}${stopped ? " stopped" : ""}`);

    return {
      changes: [{
        type: "upsert" as const,
        key: runId,
        properties: {
          "Run ID": Builder.title(runId),
          Started: Builder.dateTime(started.toISOString()),
          Status: Builder.select(status),
          Created: Builder.number(created),
          Existing: Builder.number(existing),
          Errors: Builder.number(errors.length),
        },
      }],
      hasMore: moreToFetch,
      nextState: finalState,
    };
  },
});
