import { describe, it, expect, vi, beforeEach } from 'vitest'
import { renderHook, act, waitFor } from '@testing-library/react'
import { useResourceDetail } from '../../hooks/useResourceDetail'

describe('useResourceDetail', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('loads item when id is provided', async () => {
    const item = { id: 42, title: 'My Note' }
    const fetcher = vi.fn().mockResolvedValue(item)

    const { result } = renderHook(() => useResourceDetail('42', fetcher))

    await waitFor(() => {
      expect(result.current.loading).toBe(false)
    })

    expect(result.current.item).toEqual(item)
    expect(result.current.error).toBeNull()
    expect(fetcher).toHaveBeenCalledWith('42')
  })

  it('does not call fetcher when id is undefined', async () => {
    const fetcher = vi.fn().mockResolvedValue({ id: 1 })

    const { result } = renderHook(() => useResourceDetail(undefined, fetcher))

    // Give it a tick to settle
    await act(async () => {
      await new Promise((r) => setTimeout(r, 10))
    })

    expect(fetcher).not.toHaveBeenCalled()
    expect(result.current.item).toBeNull()
  })

  it('sets error state when fetcher rejects', async () => {
    const fetcher = vi.fn().mockRejectedValue(new Error('Not found'))

    const { result } = renderHook(() => useResourceDetail('99', fetcher))

    await waitFor(() => {
      expect(result.current.loading).toBe(false)
    })

    expect(result.current.error).toBe('Not found')
    expect(result.current.item).toBeNull()
  })

  it('sets generic error for non-Error rejections', async () => {
    const fetcher = vi.fn().mockRejectedValue('oops')

    const { result } = renderHook(() => useResourceDetail('1', fetcher))

    await waitFor(() => {
      expect(result.current.loading).toBe(false)
    })

    expect(result.current.error).toBe('Failed to load')
  })

  it('refresh() re-calls fetcher with the same id', async () => {
    const item = { id: 5 }
    const fetcher = vi.fn().mockResolvedValue(item)

    const { result } = renderHook(() => useResourceDetail('5', fetcher))

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
    expect(fetcher).toHaveBeenNthCalledWith(2, '5')
  })
})
