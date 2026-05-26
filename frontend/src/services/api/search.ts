import type { SearchResult } from '../../types'
import { API_BASE, fetchWithErrorHandling, handleResponse } from './client'

export async function globalSearch(params: {
  q?: string
  tags?: string[]
  types?: string[]
}): Promise<SearchResult[]> {
  const p = new URLSearchParams()
  if (params.q) p.set('q', params.q)
  if (params.tags?.length) params.tags.forEach((t) => p.append('tag', t))
  if (params.types?.length) params.types.forEach((t) => p.append('type', t))
  const query = p.toString() ? `?${p.toString()}` : ''
  const response = await fetchWithErrorHandling(`${API_BASE}/search${query}`)
  return handleResponse<SearchResult[]>(response)
}
