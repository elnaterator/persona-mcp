import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import type { Communication, Contact } from '../../types'
import {
  addContactCommunication,
  createContact,
  deleteContact,
  getContact,
  listContactCommunications,
  listContacts,
  removeContactCommunication,
  searchCommunications,
  updateContact,
  updateContactCommunication,
} from '../../services/api'

export interface ContactFilters {
  tags?: string[]
  q?: string
}

export const contactKeys = {
  all: ['contacts'] as const,
  lists: () => [...contactKeys.all, 'list'] as const,
  list: (filters?: ContactFilters) =>
    [...contactKeys.lists(), filters ?? {}] as const,
  details: () => [...contactKeys.all, 'detail'] as const,
  detail: (id: number) => [...contactKeys.details(), id] as const,
  comms: (id: number) => [...contactKeys.detail(id), 'communications'] as const,
}

export const communicationKeys = {
  all: ['communications'] as const,
  search: (q?: string, tags?: string[]) =>
    [...communicationKeys.all, 'search', { q: q ?? '', tags: tags ?? [] }] as const,
}

export function useContactList(filters?: ContactFilters) {
  return useQuery({
    queryKey: contactKeys.list(filters),
    queryFn: () =>
      listContacts(
        filters?.tags?.length ? filters.tags : undefined,
        filters?.q || undefined,
      ),
  })
}

export function useContactDetail(id: number | undefined) {
  return useQuery({
    queryKey: id ? contactKeys.detail(id) : contactKeys.details(),
    queryFn: () => getContact(id!),
    enabled: !!id,
  })
}

export function useContactMutations() {
  const qc = useQueryClient()
  const create = useMutation({
    mutationFn: (data: Partial<Contact>) => createContact(data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: contactKeys.lists() })
      qc.invalidateQueries({ queryKey: ['tags'] })
    },
  })
  const update = useMutation({
    mutationFn: ({ id, data }: { id: number; data: Partial<Contact> }) =>
      updateContact(id, data),
    onSuccess: (_d, { id }) => {
      qc.invalidateQueries({ queryKey: contactKeys.lists() })
      qc.invalidateQueries({ queryKey: contactKeys.detail(id) })
      qc.invalidateQueries({ queryKey: ['tags'] })
    },
  })
  const remove = useMutation({
    mutationFn: (id: number) => deleteContact(id),
    onSuccess: (_d, id) => {
      qc.invalidateQueries({ queryKey: contactKeys.lists() })
      qc.removeQueries({ queryKey: contactKeys.detail(id) })
    },
  })
  return { create, update, remove }
}

export function useContactCommunications(contactId: number | undefined) {
  return useQuery({
    queryKey: contactId ? contactKeys.comms(contactId) : ['contacts', 'comms', null],
    queryFn: () => listContactCommunications(contactId!),
    enabled: !!contactId,
  })
}

export function useCommunicationMutations() {
  const qc = useQueryClient()
  const invalidateContactComms = (contactId: number) => {
    qc.invalidateQueries({ queryKey: contactKeys.comms(contactId) })
    qc.invalidateQueries({ queryKey: communicationKeys.all })
  }
  const add = useMutation({
    mutationFn: ({ contactId, data }: { contactId: number; data: Partial<Communication> }) =>
      addContactCommunication(contactId, data),
    onSuccess: (_d, { contactId }) => invalidateContactComms(contactId),
  })
  const update = useMutation({
    mutationFn: ({
      contactId,
      commId,
      data,
    }: {
      contactId: number
      commId: number
      data: Partial<Communication>
    }) => updateContactCommunication(contactId, commId, data),
    onSuccess: (_d, { contactId }) => invalidateContactComms(contactId),
  })
  const remove = useMutation({
    mutationFn: ({ contactId, commId }: { contactId: number; commId: number }) =>
      removeContactCommunication(contactId, commId),
    onSuccess: (_d, { contactId }) => invalidateContactComms(contactId),
  })
  return { add, update, remove }
}

export function useCommunicationSearch(params: { q?: string; tags?: string[]; enabled?: boolean }) {
  const { q, tags, enabled = true } = params
  return useQuery({
    queryKey: communicationKeys.search(q, tags),
    queryFn: () => searchCommunications({ q, tags }),
    enabled: enabled && (!!q?.trim() || !!tags?.length),
  })
}
