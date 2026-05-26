import { useQuery } from '@tanstack/react-query'
import { globalSearch } from '../../services/api'

export interface GlobalSearchParams {
  q?: string
  tags?: string[]
  types?: string[]
  enabled?: boolean
}

export const searchKeys = {
  all: ['search'] as const,
  search: (params: Omit<GlobalSearchParams, 'enabled'>) =>
    [...searchKeys.all, params] as const,
}

export function useGlobalSearch({ q, tags, types, enabled = true }: GlobalSearchParams) {
  const hasInput = !!q || !!(tags && tags.length > 0)
  return useQuery({
    queryKey: searchKeys.search({ q, tags, types }),
    queryFn: () => globalSearch({ q, tags, types }),
    enabled: enabled && hasInput,
  })
}
