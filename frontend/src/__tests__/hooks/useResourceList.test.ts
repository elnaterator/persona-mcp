import { describe, it, expect, vi, beforeEach } from 'vitest'
import { renderHook, act, waitFor } from '@testing-library/react'
import { useResourceList } from '../../hooks/useResourceList'

describe('useResourceList', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('returns items after successful fetch', async () => {
    const items = [{ id: 1 }, { id: 2 }]
    const fetcher = vi.fn().mockResolvedValue(items)

    const { result } = renderHook(() => useResourceList(fetcher))

    await waitFor(() => {
      expect(result.current.loading).toBe(false)
    })

    expect(result.current.items).toEqual(items)
    expect(result.current.error).toBeNull()
  })

  it('starts with loading=true and transitions to false', async () => {
    let resolve!: (v: unknown[]) => void
    const fetcher = vi.fn().mockReturnValue(new Promise((res) => { resolve = res }))

    const { result } = renderHook(() => useResourceList(fetcher))

    expect(result.current.loading).toBe(true)

    await act(async () => {
      resolve([])
    })

    expect(result.current.loading).toBe(false)
  })

  it('sets error state when fetcher rejects', async () => {
    const fetcher = vi.fn().mockRejectedValue(new Error('Network error'))

    const { result } = renderHook(() => useResourceList(fetcher))

    await waitFor(() => {
      expect(result.current.loading).toBe(false)
    })

    expect(result.current.error).toBe('Network error')
    expect(result.current.items).toEqual([])
  })

  it('sets generic error message for non-Error rejections', async () => {
    const fetcher = vi.fn().mockRejectedValue('unexpected failure')

    const { result } = renderHook(() => useResourceList(fetcher))

    await waitFor(() => {
      expect(result.current.loading).toBe(false)
    })

    expect(result.current.error).toBe('Failed to load')
  })

  it('refresh() re-calls the fetcher', async () => {
    const items = [{ id: 1 }]
    const fetcher = vi.fn().mockResolvedValue(items)

    const { result } = renderHook(() => useResourceList(fetcher))

    await waitFor(() => {
      expect(result.current.loading).toBe(false)
    })

    expect(fetcher).toHaveBeenCalledTimes(1)

    await act(async () => {
      result.current.refresh()
    })

    await waitFor(() => {
      expect(result.current.loading).toBe(false)
    })

    expect(fetcher).toHaveBeenCalledTimes(2)
  })
})
