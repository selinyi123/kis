import test from "node:test";
import assert from "node:assert/strict";
import { toNotionProperties } from "../src/notion-map.js";

test("maps an external starred repo", () => {
  const properties = toNotionProperties({
    starredAt: "2026-08-30T08:00:00Z",
    fullName: "openai/example",
    owner: "openai",
    description: "Example project",
    stars: 42,
    htmlUrl: "https://github.com/openai/example",
    topics: ["ai"],
  }, new Date("2026-08-30T09:00:00Z"));

  assert.equal(properties["名称"].title[0].text.content, "openai/example");
  assert.equal(properties["Star 数"].number, 42);
  assert.equal(properties["归属"].select.name, "外部");
  assert.equal(properties["抓取日期"].date.start, "2026-08-30");
  assert.equal(properties["链接"].url, "https://github.com/openai/example");
});
