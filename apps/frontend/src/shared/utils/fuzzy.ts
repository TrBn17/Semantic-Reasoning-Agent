const DIACRITICS_REGEX = /[\u0300-\u036f]/g;

export function normalizeSearch(value: string): string {
  return value
    .normalize("NFD")
    .replace(DIACRITICS_REGEX, "")
    .toLowerCase()
    .trim();
}

function subsequenceScore(query: string, target: string): number {
  if (!query) return 0;
  let tIndex = 0;
  let matched = 0;
  let streak = 0;
  let bestStreak = 0;

  for (let qIndex = 0; qIndex < query.length; qIndex += 1) {
    const needle = query[qIndex];
    const foundAt = target.indexOf(needle, tIndex);
    if (foundAt === -1) {
      return 0;
    }
    if (foundAt === tIndex) {
      streak += 1;
      bestStreak = Math.max(bestStreak, streak);
    } else {
      streak = 1;
      bestStreak = Math.max(bestStreak, streak);
    }
    matched += 1;
    tIndex = foundAt + 1;
  }

  return matched * 10 + bestStreak * 2;
}

export function scoreMatch(query: string, target: string): number {
  const q = normalizeSearch(query);
  const t = normalizeSearch(target);
  if (!q || !t) return 0;
  if (q === t) return 1000;
  if (t.startsWith(q)) return 700 - (t.length - q.length);
  const index = t.indexOf(q);
  if (index >= 0) {
    return 500 - index;
  }
  return subsequenceScore(q, t);
}

export function rankItems<T>(
  items: T[],
  query: string,
  selectFields: (item: T) => Array<string | number | null | undefined>,
): Array<{ item: T; score: number }> {
  const normalizedQuery = normalizeSearch(query);
  if (!normalizedQuery) {
    return items.map((item) => ({ item, score: 0 }));
  }

  const ranked = items
    .map((item) => {
      const score = selectFields(item).reduce<number>((best, value) => {
        if (value === null || value === undefined) return best;
        return Math.max(best, scoreMatch(normalizedQuery, String(value)));
      }, 0);
      return { item, score };
    })
    .filter((entry) => entry.score > 0)
    .sort((a, b) => b.score - a.score);
  return ranked;
}
