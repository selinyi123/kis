export interface DeltaState {
  lastStarredAt?: string;
  page?: number;
  cycleNewest?: string;
}

export function isNewStar(starredAt: string, lastStarredAt?: string): boolean {
  return !lastStarredAt || starredAt > lastStarredAt;
}

export function newestStarredAt(current: string | undefined, candidate: string): string {
  return !current || candidate > current ? candidate : current;
}
