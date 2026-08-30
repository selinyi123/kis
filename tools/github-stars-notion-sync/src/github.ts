import type { StarredRepo } from "./model.js";

const API = "https://api.github.com";
const RETRYABLE = new Set([408, 429, 500, 502, 503, 504]);

export interface StarredPage {
  items: StarredRepo[];
  hasNextPage: boolean;
}

async function request(path: string, token: string): Promise<Response> {
  let lastError: unknown;
  for (let attempt = 0; attempt < 3; attempt++) {
    try {
      const response = await fetch(`${API}${path}`, {
        headers: {
          Authorization: `Bearer ${token}`,
          Accept: "application/vnd.github.star+json",
          "X-GitHub-Api-Version": "2022-11-28",
          "User-Agent": "selinyi123-github-stars-notion-sync",
        },
        signal: AbortSignal.timeout(15_000),
      });

      if (response.ok) return response;
      if (!RETRYABLE.has(response.status) || attempt === 2) {
        throw new Error(`GitHub ${path} -> ${response.status}: ${(await response.text()).slice(0, 300)}`);
      }

      const retryAfter = Number(response.headers.get("retry-after"));
      const delayMs = Number.isFinite(retryAfter) && retryAfter > 0
        ? Math.min(retryAfter * 1000, 30_000)
        : 1000 * (attempt + 1);
      await new Promise((resolve) => setTimeout(resolve, delayMs));
    } catch (error) {
      lastError = error;
      if (attempt === 2) throw error;
      await new Promise((resolve) => setTimeout(resolve, 1000 * (attempt + 1)));
    }
  }
  throw lastError instanceof Error ? lastError : new Error("GitHub request failed");
}

export async function getStarredPage(
  token: string,
  page: number,
  perPage: number,
): Promise<StarredPage> {
  const response = await request(`/user/starred?per_page=${perPage}&page=${page}&sort=created&direction=desc`, token);
  const body = await response.json() as Array<{
    starred_at: string;
    repo: {
      full_name: string;
      description: string | null;
      stargazers_count: number;
      html_url: string;
      topics?: string[];
      owner: { login: string };
    };
  }>;

  return {
    items: body.map(({ starred_at, repo }) => ({
      starredAt: starred_at,
      fullName: repo.full_name,
      owner: repo.owner.login,
      description: repo.description ?? null,
      stars: repo.stargazers_count ?? 0,
      htmlUrl: repo.html_url,
      topics: Array.isArray(repo.topics) ? repo.topics : [],
    })),
    hasNextPage: /rel="next"/.test(response.headers.get("link") ?? ""),
  };
}
