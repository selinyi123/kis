export interface StarredRepo {
  starredAt: string;
  fullName: string;
  owner: string;
  description: string | null;
  stars: number;
  htmlUrl: string;
  topics: string[];
}
