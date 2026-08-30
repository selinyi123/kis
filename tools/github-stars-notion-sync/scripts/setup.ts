import { Client } from "@notionhq/client";
import { spawnSync } from "node:child_process";
import * as fs from "node:fs";
import * as readline from "node:readline/promises";

import { CONFIG } from "../src/config.js";
import { NOTION_VERSION } from "../src/notion.js";

const CALLBACK_URL = "https://www.notion.so/workers/oauth/callback";

function runNtn(args: string[], quiet = false) {
  const result = spawnSync("ntn", args, {
    stdio: quiet ? "ignore" : "inherit",
    encoding: "utf8",
  });
  if (result.status !== 0) throw new Error(`ntn ${args.join(" ")} failed`);
}

function hasNtn() {
  return spawnSync("ntn", ["--version"], { stdio: "ignore" }).status === 0;
}

function ntnAuthed() {
  const result = spawnSync("ntn", ["doctor"], { encoding: "utf8" });
  const output = `${result.stdout ?? ""}${result.stderr ?? ""}`;
  return result.status === 0 && /Token valid\s+✔/.test(output);
}

function readEnv(): Record<string, string> {
  if (!fs.existsSync(".env")) return {};
  return Object.fromEntries(
    fs.readFileSync(".env", "utf8")
      .split("\n")
      .map((line) => /^\s*([A-Z0-9_]+)\s*=\s*(.*)\s*$/.exec(line))
      .filter((match): match is RegExpExecArray => !!match)
      .map((match) => [match[1], match[2].replace(/^["']|["']$/g, "")]),
  );
}

function writeEnv(values: Record<string, string>) {
  fs.writeFileSync(
    ".env",
    Object.entries(values).filter(([, value]) => value).map(([key, value]) => `${key}=${value}`).join("\n") + "\n",
  );
}

async function main() {
  if (!hasNtn()) {
    throw new Error("Notion CLI `ntn` is required. Install it first, then rerun `npm run setup`.");
  }
  if (!ntnAuthed()) runNtn(["login"]);

  const previous = readEnv();
  const rl = readline.createInterface({ input: process.stdin, output: process.stdout });

  let notionToken = previous.NOTION_API_TOKEN ?? "";
  if (!notionToken) notionToken = (await rl.question("Notion PAT (ntn_...): ")).trim();
  if (!notionToken) throw new Error("NOTION_API_TOKEN is required");

  const notion = new Client({ auth: notionToken, notionVersion: NOTION_VERSION });
  const dataSource = await notion.request({
    path: `data_sources/${CONFIG.dataSourceId}`,
    method: "get",
  }) as { id?: string };
  if (!dataSource.id) throw new Error(`Cannot access Notion data source ${CONFIG.dataSourceId}`);
  console.log(`✓ Notion target verified: ${CONFIG.dataSourceId}`);

  let clientId = previous.GITHUB_CLIENT_ID ?? "";
  let clientSecret = previous.GITHUB_CLIENT_SECRET ?? "";
  if (!clientId || !clientSecret) {
    console.log("\nCreate one GitHub OAuth App:");
    console.log("  https://github.com/settings/applications/new");
    console.log("  Application name: gh-stars-notion-sync");
    console.log("  Homepage URL: https://github.com");
    console.log(`  Authorization callback URL: ${CALLBACK_URL}\n`);
  }
  if (!clientId) clientId = (await rl.question("GitHub OAuth Client ID: ")).trim();
  if (!clientSecret) clientSecret = (await rl.question("GitHub OAuth Client Secret: ")).trim();
  if (!clientId || !clientSecret) throw new Error("GitHub OAuth credentials are required");

  writeEnv({
    NOTION_API_TOKEN: notionToken,
    REPOS_DATA_SOURCE_ID: CONFIG.dataSourceId,
    GITHUB_CLIENT_ID: clientId,
    GITHUB_CLIENT_SECRET: clientSecret,
    GITHUB_PER_PAGE: previous.GITHUB_PER_PAGE ?? "20",
  });

  if (!fs.existsSync("workers.json")) {
    runNtn(["workers", "create", "--name", "github-stars-notion-sync"]);
  }
  runNtn(["workers", "deploy"]);
  runNtn(["workers", "env", "push", "--yes"]);
  console.log("✓ Worker deployed");

  runNtn(["workers", "oauth", "start", "githubAuth"]);
  await rl.question("Approve GitHub read:user access in the opened browser, then press Enter here...");
  rl.close();

  runNtn(["workers", "sync", "trigger", "githubStarsDelta"]);
  console.log("✓ Initial sync triggered. Future delta syncs run every 10 minutes.");
}

main().catch((error) => {
  console.error(error instanceof Error ? error.message : error);
  process.exit(1);
});
