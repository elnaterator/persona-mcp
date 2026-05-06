import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { renderHook, act } from '@testing-library/react'
import { useStatusMessage } from '../../hooks/useStatusMessage'

describe('useStatusMessage', () => {
  beforeEach(() => {
    vi.useFakeTimers()
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  it('showMessage sets message and defaults isError to false', () => {
    const { result } = renderHook(() => useStatusMessage())

    act(() => {
      result.current.showMessage('Saved successfully')
    })

    expect(result.current.message).toBe('Saved successfully')
    expect(result.current.isError).toBe(false)
  })

  it('showMessage with error=true sets isError to true', () => {
    const { result } = renderHook(() => useStatusMessage())

    act(() => {
      result.current.showMessage('Something went wrong', true)
    })

    expect(result.current.message).toBe('Something went wrong')
    expect(result.current.isError).toBe(true)
  })

  it('clearMessage resets message and isError', () => {
    const { result } = renderHook(() => useStatusMessage())

    act(() => {
      result.current.showMessage('Hello', true)
    })

    expect(result.current.message).toBe('Hello')

    act(() => {
      result.current.clearMessage()
    })

    expect(result.current.message).toBeNull()
    expect(result.current.isError).toBe(false)
  })

  it('auto-dismisses after the specified timeout', () => {
    const { result } = renderHook(() => useStatusMessage())

    act(() => {
      result.current.showMessage('Flash message', false, 2000)
    })

    expect(result.current.message).toBe('Flash message')

    act(() => {
      vi.advanceTimersByTime(2000)
    })

    expect(result.current.message).toBeNull()
    expect(result.current.isError).toBe(false)
  })

  it('does not auto-dismiss when autoDismissMs is 0', () => {
    const { result } = renderHook(() => useStatusMessage())

    act(() => {
      result.current.showMessage('Sticky message', false, 0)
    })

    act(() => {
      vi.advanceTimersByTime(10000)
    })

    expect(result.current.message).toBe('Sticky message')
  })

  it('calling showMessage again resets the timer', () => {
    const { result } = renderHook(() => useStatusMessage())

    act(() => {
      result.current.showMessage('First', false, 1000)
    })

    // Advance partway through the first timer
    act(() => {
      vi.advanceTimersByTime(500)
    })

    // Show a second message — resets the timer
    act(() => {
      result.current.showMessage('Second', false, 1000)
    })

    // Advance 600ms more (total 1100ms since first, but only 600ms since second)
    act(() => {
      vi.advanceTimersByTime(600)
    })

    // Second message should still be visible (timer reset on second call)
    expect(result.current.message).toBe('Second')

    // Advance the remaining 400ms for the second timer
    act(() => {
      vi.advanceTimersByTime(400)
    })

    expect(result.current.message).toBeNull()
  })
})
