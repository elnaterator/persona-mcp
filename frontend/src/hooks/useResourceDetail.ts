import { useState, useEffect, useCallback } from 'react'

export interface ResourceDetailState<T> {
  item: T | null
  loading: boolean
  error: string | null
  refresh: () => void
  setItem: (item: T | null) => void
}

export function useResourceDetail<T>(
  id: string | undefined,
  fetcher: (id: string) => Promise<T>
): ResourceDetailState<T> {
  const [item, setItem] = useState<T | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const load = useCallback(async () => {
    if (!id) return
    setLoading(true)
    setError(null)
    try {
      const data = await fetcher(id)
      setItem(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load')
    } finally {
      setLoading(false)
    }
  }, [id, fetcher])

  useEffect(() => { load() }, [load])

  return { item, loading, error, refresh: load, setItem }
}
