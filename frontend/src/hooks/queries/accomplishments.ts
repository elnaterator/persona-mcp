import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import type { Accomplishment } from '../../types'
import {
  createAccomplishment,
  deleteAccomplishment,
  getAccomplishment,
  listAccomplishments,
  updateAccomplishment,
} from '../../services/api'

export interface AccomplishmentFilters {
  tags?: string[]
  q?: string
}

export const accomplishmentKeys = {
  all: ['accomplishments'] as const,
  lists: () => [...accomplishmentKeys.all, 'list'] as const,
  list: (filters?: AccomplishmentFilters) =>
    [...accomplishmentKeys.lists(), filters ?? {}] as const,
  details: () => [...accomplishmentKeys.all, 'detail'] as const,
  detail: (id: number) => [...accomplishmentKeys.details(), id] as const,
}

export function useAccomplishmentList(filters?: AccomplishmentFilters) {
  return useQuery({
    queryKey: accomplishmentKeys.list(filters),
    queryFn: () =>
      listAccomplishments(
        filters?.tags?.length ? filters.tags : undefined,
        filters?.q || undefined,
      ),
  })
}

export function useAccomplishmentDetail(id: number | undefined) {
  return useQuery({
    queryKey: id ? accomplishmentKeys.detail(id) : accomplishmentKeys.details(),
    queryFn: () => getAccomplishment(id!),
    enabled: !!id,
  })
}

export function useAccomplishmentMutations() {
  const qc = useQueryClient()
  const create = useMutation({
    mutationFn: (data: Partial<Accomplishment>) => createAccomplishment(data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: accomplishmentKeys.lists() })
      qc.invalidateQueries({ queryKey: ['tags'] })
    },
  })
  const update = useMutation({
    mutationFn: ({ id, data }: { id: number; data: Partial<Accomplishment> }) =>
      updateAccomplishment(id, data),
    onSuccess: (_d, { id }) => {
      qc.invalidateQueries({ queryKey: accomplishmentKeys.lists() })
      qc.invalidateQueries({ queryKey: accomplishmentKeys.detail(id) })
      qc.invalidateQueries({ queryKey: ['tags'] })
    },
  })
  const remove = useMutation({
    mutationFn: (id: number) => deleteAccomplishment(id),
    onSuccess: (_d, id) => {
      qc.invalidateQueries({ queryKey: accomplishmentKeys.lists() })
      qc.removeQueries({ queryKey: accomplishmentKeys.detail(id) })
    },
  })
  return { create, update, remove }
}
