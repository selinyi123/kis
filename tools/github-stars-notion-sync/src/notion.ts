import { Client } from "@notionhq/client";
import type { StarredRepo } from "./model.js";
import { toNotionProperties } from "./notion-map.js";

export const NOTION_VERSION = "2026-03-11";

interface NotionPageRef {
  id: string;
  created_time?: string;
}

async function query(
  notion: Client,
  dataSourceId: string,
  filter: Record<string, unknown>,
): Promise<NotionPageRef[]> {
  const response = await notion.request({
    path: `data_sources/${dataSourceId}/query`,
    method: "post",
    body: { page_size: 10, filter },
  }) as { results?: NotionPageRef[] };
  return response.results ?? [];
}

async function findExisting(
  notion: Client,
  dataSourceId: string,
  repo: StarredRepo,
): Promise<NotionPageRef[]> {
  const byUrl = await query(notion, dataSourceId, {
    property: "链接",
    url: { equals: repo.htmlUrl },
  });
  if (byUrl.length) return byUrl;

  return query(notion, dataSourceId, {
    property: "名称",
    title: { equals: repo.fullName },
  });
}

export async function ensureRepoRow(
  notion: Client,
  dataSourceId: string,
  repo: StarredRepo,
): Promise<"created" | "exists"> {
  if ((await findExisting(notion, dataSourceId, repo)).length) return "exists";

  await notion.request({
    path: "pages",
    method: "post",
    body: {
      parent: { data_source_id: dataSourceId },
      properties: toNotionProperties(repo),
    },
  });

  // A later retry is safe because every run queries exact URL/name first.
  return "created";
}

export function createNotionClient(token: string): Client {
  return new Client({ auth: token, notionVersion: NOTION_VERSION });
}
