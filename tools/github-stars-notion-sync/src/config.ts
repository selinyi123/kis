export const CONFIG = {
  ownerLogin: "selinyi123",
  dataSourceId: process.env.REPOS_DATA_SOURCE_ID ?? "1c42c531-4691-4911-bccf-630a9366f744",
  perPage: Math.min(100, Math.max(1, Number(process.env.GITHUB_PER_PAGE ?? "20"))),
  timezone: "Asia/Taipei",
} as const;
