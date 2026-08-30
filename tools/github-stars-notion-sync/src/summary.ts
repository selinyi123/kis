export function summarizePurpose(description: string | null, topics: string[]): string {
  const base = description?.trim();
  if (base) return base.length <= 120 ? base : `${base.slice(0, 117)}…`;
  if (topics.length) return `围绕 ${topics.slice(0, 4).join("、")} 的开源项目。`;
  return "";
}
