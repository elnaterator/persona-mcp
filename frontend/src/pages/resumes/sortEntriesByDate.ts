interface DatedEntry {
  start_date: string | null
  end_date: string | null
}

function dateValue(date: string | null): number {
  if (!date) return Number.NEGATIVE_INFINITY
  const parsed = Date.parse(date)
  return Number.isNaN(parsed) ? Number.NEGATIVE_INFINITY : parsed
}

export interface IndexedEntry<T> {
  entry: T
  index: number
}

/** Sorts entries most-recent-first; entries with no end date (ongoing) sort to the top. */
export function sortEntriesByDate<T extends DatedEntry>(entries: T[]): IndexedEntry<T>[] {
  return entries
    .map((entry, index) => ({ entry, index }))
    .sort((a, b) => {
      const aEnd = a.entry.end_date === null ? Number.POSITIVE_INFINITY : dateValue(a.entry.end_date)
      const bEnd = b.entry.end_date === null ? Number.POSITIVE_INFINITY : dateValue(b.entry.end_date)
      if (aEnd !== bEnd) return bEnd - aEnd
      return dateValue(b.entry.start_date) - dateValue(a.entry.start_date)
    })
}
