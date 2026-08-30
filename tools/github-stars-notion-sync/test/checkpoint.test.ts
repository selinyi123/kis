import test from "node:test";
import assert from "node:assert/strict";
import { isNewStar, newestStarredAt } from "../src/checkpoint.js";

test("stops at previous checkpoint", () => {
  assert.equal(isNewStar("2026-08-30T10:00:00Z", "2026-08-30T09:00:00Z"), true);
  assert.equal(isNewStar("2026-08-30T09:00:00Z", "2026-08-30T09:00:00Z"), false);
  assert.equal(isNewStar("2026-08-30T08:00:00Z", "2026-08-30T09:00:00Z"), false);
});

test("tracks newest timestamp", () => {
  assert.equal(newestStarredAt("2026-08-30T09:00:00Z", "2026-08-30T10:00:00Z"), "2026-08-30T10:00:00Z");
});
