import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import type { Note } from '../../types'
import {
  createNote,
  deleteNote,
  getNote,
  listNotes,
  updateNote,
} from '../../services/api'

export interface NoteFilters {
  tags?: string[]
  q?: string
}

export const noteKeys = {
  all: ['notes'] as const,
  lists: () => [...noteKeys.all, 'list'] as const,
  list: (filters?: NoteFilters) => [...noteKeys.lists(), filters ?? {}] as const,
  details: () => [...noteKeys.all, 'detail'] as const,
  detail: (id: number) => [...noteKeys.details(), id] as const,
}

export function useNoteList(filters?: NoteFilters) {
  return useQuery({
    queryKey: noteKeys.list(filters),
    queryFn: () =>
      listNotes(
        filters?.tags?.length ? filters.tags : undefined,
        filters?.q || undefined,
      ),
  })
}

export function useNoteDetail(id: number | undefined) {
  return useQuery({
    queryKey: id ? noteKeys.detail(id) : noteKeys.details(),
    queryFn: () => getNote(id!),
    enabled: !!id,
  })
}

export function useNoteMutations() {
  const qc = useQueryClient()
  const create = useMutation({
    mutationFn: (data: Partial<Note>) => createNote(data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: noteKeys.lists() })
      qc.invalidateQueries({ queryKey: ['tags'] })
    },
  })
  const update = useMutation({
    mutationFn: ({ id, data }: { id: number; data: Partial<Note> }) =>
      updateNote(id, data),
    onSuccess: (_d, { id }) => {
      qc.invalidateQueries({ queryKey: noteKeys.lists() })
      qc.invalidateQueries({ queryKey: noteKeys.detail(id) })
      qc.invalidateQueries({ queryKey: ['tags'] })
    },
  })
  const remove = useMutation({
    mutationFn: (id: number) => deleteNote(id),
    onSuccess: (_d, id) => {
      qc.invalidateQueries({ queryKey: noteKeys.lists() })
      qc.removeQueries({ queryKey: noteKeys.detail(id) })
    },
  })
  return { create, update, remove }
}
