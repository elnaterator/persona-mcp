import { describe, expect, it, vi, beforeEach } from 'vitest'
import { act, renderHook } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import type { ReactNode } from 'react'
import { useLinkMutations } from '../../../hooks/queries/links'
import { applicationKeys } from '../../../hooks/queries/applications'
import { resumeKeys } from '../../../hooks/queries/resumes'

vi.mock('../../../services/api', () => ({
  linkResources: vi.fn(),
  unlinkResources: vi.fn(),
}))

import { linkResources, unlinkResources } from '../../../services/api'

function makeClient(): QueryClient {
  return new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  })
}

beforeEach(() => vi.clearAllMocks())

describe('useLinkMutations', () => {
  it('link invalidates both sides', async () => {
    vi.mocked(linkResources).mockResolvedValue({ success: true } as never)
    const client = makeClient()
    const spy = vi.spyOn(client, 'invalidateQueries')
    const wrapper = ({ children }: { children: ReactNode }) => (
      <QueryClientProvider client={client}>{children}</QueryClientProvider>
    )
    const { result } = renderHook(() => useLinkMutations(), { wrapper })
    await act(async () => {
      await result.current.link.mutateAsync({
        aType: 'application',
        aId: 1,
        bType: 'resume',
        bId: 2,
      })
    })
    expect(spy).toHaveBeenCalledWith({ queryKey: applicationKeys.detail(1) })
    expect(spy).toHaveBeenCalledWith({ queryKey: resumeKeys.detail(2) })
  })

  it('unlink invalidates both sides', async () => {
    vi.mocked(unlinkResources).mockResolvedValue(undefined as never)
    const client = makeClient()
    const spy = vi.spyOn(client, 'invalidateQueries')
    const wrapper = ({ children }: { children: ReactNode }) => (
      <QueryClientProvider client={client}>{children}</QueryClientProvider>
    )
    const { result } = renderHook(() => useLinkMutations(), { wrapper })
    await act(async () => {
      await result.current.unlink.mutateAsync({
        aType: 'application',
        aId: 3,
        bType: 'resume',
        bId: 4,
      })
    })
    expect(spy).toHaveBeenCalledWith({ queryKey: applicationKeys.detail(3) })
    expect(spy).toHaveBeenCalledWith({ queryKey: resumeKeys.detail(4) })
  })
})
