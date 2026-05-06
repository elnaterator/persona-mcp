// Generic hook for list pages: loading, error, data, refresh
import { useState, useEffect, useCallback } from 'react'

export interface ResourceListState<T> {
  items: T[]
  loading: boolean
  error: string | null
  refresh: () => void
}

export function useResourceList<T>(fetcher: () => Promise<T[]>): ResourceListState<T> {
  const [items, setItems] = useState<T[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const load = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await fetcher()
      setItems(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load')
    } finally {
      setLoading(false)
    }
  }, [fetcher])

  useEffect(() => { load() }, [load])

  return { items, loading, error, refresh: load }
}
