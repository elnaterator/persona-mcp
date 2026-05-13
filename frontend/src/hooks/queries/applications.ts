import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import type { Application } from '../../types'
import {
  createApplication,
  deleteApplication,
  getApplication,
  listApplications,
  updateApplication,
} from '../../services/api'

export interface ApplicationFilters {
  status?: string
  q?: string
  tags?: string[]
}

export const applicationKeys = {
  all: ['applications'] as const,
  lists: () => [...applicationKeys.all, 'list'] as const,
  list: (filters?: ApplicationFilters) =>
    [...applicationKeys.lists(), filters ?? {}] as const,
  details: () => [...applicationKeys.all, 'detail'] as const,
  detail: (id: number) => [...applicationKeys.details(), id] as const,
}

export function useApplicationList(filters?: ApplicationFilters) {
  return useQuery({
    queryKey: applicationKeys.list(filters),
    queryFn: () =>
      listApplications(
        filters?.status || undefined,
        filters?.q || undefined,
        filters?.tags?.length ? filters.tags : undefined,
      ),
  })
}

export function useApplicationDetail(id: number | undefined) {
  return useQuery({
    queryKey: id ? applicationKeys.detail(id) : applicationKeys.details(),
    queryFn: () => getApplication(id!),
    enabled: !!id,
  })
}

export function useApplicationMutations() {
  const qc = useQueryClient()
  const create = useMutation({
    mutationFn: (data: Partial<Application>) => createApplication(data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: applicationKeys.lists() })
      qc.invalidateQueries({ queryKey: ['tags'] })
    },
  })
  const update = useMutation({
    mutationFn: ({ id, data }: { id: number; data: Partial<Application> }) =>
      updateApplication(id, data),
    onSuccess: (_d, { id }) => {
      qc.invalidateQueries({ queryKey: applicationKeys.lists() })
      qc.invalidateQueries({ queryKey: applicationKeys.detail(id) })
      qc.invalidateQueries({ queryKey: ['tags'] })
    },
  })
  const remove = useMutation({
    mutationFn: (id: number) => deleteApplication(id),
    onSuccess: (_d, id) => {
      qc.invalidateQueries({ queryKey: applicationKeys.lists() })
      qc.removeQueries({ queryKey: applicationKeys.detail(id) })
    },
  })
  return { create, update, remove }
}
