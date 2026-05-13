import { useQuery } from '@tanstack/react-query'
import { listAllTags } from '../../services/api'

export const tagKeys = {
  all: ['tags'] as const,
  list: () => [...tagKeys.all, 'list'] as const,
}

export function useAllTags() {
  return useQuery({
    queryKey: tagKeys.list(),
    queryFn: listAllTags,
  })
}
