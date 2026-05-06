import { useState, useEffect } from 'react'
import { listAllTags } from '../services/api'

export interface UseTagsState {
  tags: string[]
  loading: boolean
}

export function useTags(): UseTagsState {
  const [tags, setTags] = useState<string[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    listAllTags()
      .then(setTags)
      .catch(() => setTags([]))
      .finally(() => setLoading(false))
  }, [])

  return { tags, loading }
}
