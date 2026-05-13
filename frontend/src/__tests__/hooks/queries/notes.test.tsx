import { describe, expect, it, vi, beforeEach } from 'vitest'
import { act, renderHook, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import type { ReactNode } from 'react'
import {
  noteKeys,
  useNoteDetail,
  useNoteList,
  useNoteMutations,
} from '../../../hooks/queries/notes'

vi.mock('../../../services/api', () => ({
  listNotes: vi.fn(),
  getNote: vi.fn(),
  createNote: vi.fn(),
  updateNote: vi.fn(),
  deleteNote: vi.fn(),
}))

import {
  createNote,
  deleteNote,
  getNote,
  listNotes,
  updateNote,
} from '../../../services/api'

function makeClient(): QueryClient {
  return new QueryClient({
    defaultOptions: {
      queries: { retry: false, gcTime: 0, staleTime: 0 },
      mutations: { retry: false },
    },
  })
}

function makeWrapper(client: QueryClient) {
  return ({ children }: { children: ReactNode }) => (
    <QueryClientProvider client={client}>{children}</QueryClientProvider>
  )
}

const mockNote = (id: number) => ({
  id,
  title: `n${id}`,
  content: '',
  tags: [],
  created_at: '',
  updated_at: '',
  links: {},
})

beforeEach(() => {
  vi.clearAllMocks()
})

describe('useNoteList', () => {
  it('calls listNotes with filter args', async () => {
    vi.mocked(listNotes).mockResolvedValue([])
    const client = makeClient()
    const { result } = renderHook(
      () => useNoteList({ tags: ['a'], q: 'foo' }),
      { wrapper: makeWrapper(client) },
    )
    await waitFor(() => expect(result.current.isSuccess).toBe(true))
    expect(listNotes).toHaveBeenCalledWith(['a'], 'foo')
  })

  it('passes undefined when filters empty', async () => {
    vi.mocked(listNotes).mockResolvedValue([])
    const client = makeClient()
    renderHook(() => useNoteList(), { wrapper: makeWrapper(client) })
    await waitFor(() => expect(listNotes).toHaveBeenCalledTimes(1))
    expect(listNotes).toHaveBeenCalledWith(undefined, undefined)
  })
})

describe('useNoteDetail', () => {
  it('disables when id missing', () => {
    const client = makeClient()
    renderHook(() => useNoteDetail(undefined), { wrapper: makeWrapper(client) })
    expect(getNote).not.toHaveBeenCalled()
  })

  it('fetches when id present', async () => {
    vi.mocked(getNote).mockResolvedValue(mockNote(7) as never)
    const client = makeClient()
    const { result } = renderHook(() => useNoteDetail(7), {
      wrapper: makeWrapper(client),
    })
    await waitFor(() => expect(result.current.isSuccess).toBe(true))
    expect(getNote).toHaveBeenCalledWith(7)
  })
})

describe('useNoteMutations', () => {
  it('create invalidates list', async () => {
    vi.mocked(createNote).mockResolvedValue(mockNote(1) as never)
    const client = makeClient()
    const spy = vi.spyOn(client, 'invalidateQueries')
    const { result } = renderHook(() => useNoteMutations(), {
      wrapper: makeWrapper(client),
    })
    await act(async () => {
      await result.current.create.mutateAsync({ title: 't' })
    })
    expect(spy).toHaveBeenCalledWith({ queryKey: noteKeys.lists() })
  })

  it('update invalidates list and detail', async () => {
    vi.mocked(updateNote).mockResolvedValue(mockNote(5) as never)
    const client = makeClient()
    const spy = vi.spyOn(client, 'invalidateQueries')
    const { result } = renderHook(() => useNoteMutations(), {
      wrapper: makeWrapper(client),
    })
    await act(async () => {
      await result.current.update.mutateAsync({ id: 5, data: { title: 'x' } })
    })
    expect(spy).toHaveBeenCalledWith({ queryKey: noteKeys.lists() })
    expect(spy).toHaveBeenCalledWith({ queryKey: noteKeys.detail(5) })
  })

  it('remove invalidates list and removes detail', async () => {
    vi.mocked(deleteNote).mockResolvedValue({ success: true } as never)
    const client = makeClient()
    const invalidateSpy = vi.spyOn(client, 'invalidateQueries')
    const removeSpy = vi.spyOn(client, 'removeQueries')
    const { result } = renderHook(() => useNoteMutations(), {
      wrapper: makeWrapper(client),
    })
    await act(async () => {
      await result.current.remove.mutateAsync(9)
    })
    expect(invalidateSpy).toHaveBeenCalledWith({ queryKey: noteKeys.lists() })
    expect(removeSpy).toHaveBeenCalledWith({ queryKey: noteKeys.detail(9) })
  })
})
