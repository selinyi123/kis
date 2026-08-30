import { CONFIG } from "./config.js";
import type { StarredRepo } from "./model.js";
import { summarizePurpose } from "./summary.js";

function taipeiDate(now = new Date()): string {
  const parts = new Intl.DateTimeFormat("en-CA", {
    timeZone: CONFIG.timezone,
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  }).formatToParts(now);
  const values = Object.fromEntries(parts.map((part) => [part.type, part.value]));
  return `${values.year}-${values.month}-${values.day}`;
}

function richText(content: string) {
  return content
    ? { rich_text: [{ type: "text", text: { content } }] }
    : { rich_text: [] };
}

export function toNotionProperties(repo: StarredRepo, now = new Date()) {
  return {
    "名称": { title: [{ type: "text", text: { content: repo.fullName } }] },
    "Star 数": { number: repo.stars },
    "介绍": richText(repo.description ?? ""),
    "功能作用": richText(summarizePurpose(repo.description, repo.topics)),
    "归属": { select: { name: repo.owner === CONFIG.ownerLogin ? "本人" : "外部" } },
    "抓取日期": { date: { start: taipeiDate(now) } },
    "链接": { url: repo.htmlUrl },
  } as const;
}
