import { CONFIG } from "./config.js";
import type { StarredRepo } from "./model.js";
import { summarizePurpose } from "./summary.js";

function taipeiDate(now = new Date()): string {
  return new Intl.DateTimeFormat("en-CA", {
    timeZone: CONFIG.timezone,
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  }).format(now);
}

export function toNotionProperties(repo: StarredRepo, now = new Date()) {
  return {
    "名称": repo.fullName,
    "Star 数": repo.stars,
    "介绍": repo.description ?? "",
    "功能作用": summarizePurpose(repo.description, repo.topics),
    "归属": repo.owner === CONFIG.ownerLogin ? "本人" : "外部",
    "date:抓取日期:start": taipeiDate(now),
    "date:抓取日期:is_datetime": 0,
    "userDefined:链接": repo.htmlUrl,
  } as const;
}
