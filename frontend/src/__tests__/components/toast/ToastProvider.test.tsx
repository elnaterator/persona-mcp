import { act, fireEvent, render, screen } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { ToastProvider, useToast } from '../../../components/toast'

function ToastTrigger({
  onMount,
}: {
  onMount?: (api: ReturnType<typeof useToast>) => void
}) {
  const api = useToast()
  if (onMount) {
    onMount(api)
  }
  return null
}

function renderWithToast(children: React.ReactNode) {
  return render(<ToastProvider>{children}</ToastProvider>)
}

describe('ToastProvider', () => {
  beforeEach(() => {
    vi.useFakeTimers()
  })
  afterEach(() => {
    vi.useRealTimers()
  })

  it('shows a success toast', () => {
    let api: ReturnType<typeof useToast>
    renderWithToast(
      <ToastTrigger
        onMount={(a) => {
          api = a
        }}
      />,
    )
    act(() => {
      api!.success('Saved!')
    })
    expect(screen.getByText('Saved!')).toBeInTheDocument()
  })

  it('auto-dismisses after duration', () => {
    let api: ReturnType<typeof useToast>
    renderWithToast(
      <ToastTrigger
        onMount={(a) => {
          api = a
        }}
      />,
    )
    act(() => {
      api!.success('Gone soon', { duration: 1000 })
    })
    expect(screen.getByText('Gone soon')).toBeInTheDocument()

    act(() => {
      vi.runAllTimers()
    })
    expect(screen.queryByText('Gone soon')).not.toBeInTheDocument()
  })

  it('replaces existing toast with same id', () => {
    let api: ReturnType<typeof useToast>
    renderWithToast(
      <ToastTrigger
        onMount={(a) => {
          api = a
        }}
      />,
    )
    act(() => {
      api!.success('Saving…', { id: 'save', duration: Infinity })
    })
    expect(screen.getByText('Saving…')).toBeInTheDocument()

    act(() => {
      api!.success('Saved', { id: 'save' })
    })
    expect(screen.queryByText('Saving…')).not.toBeInTheDocument()
    expect(screen.getByText('Saved')).toBeInTheDocument()
  })

  it('evicts oldest toast when max=3 is exceeded', () => {
    let api: ReturnType<typeof useToast>
    renderWithToast(
      <ToastTrigger
        onMount={(a) => {
          api = a
        }}
      />,
    )
    act(() => {
      api!.success('First', { duration: Infinity })
      api!.success('Second', { duration: Infinity })
      api!.success('Third', { duration: Infinity })
    })
    expect(screen.getByText('First')).toBeInTheDocument()
    expect(screen.getByText('Second')).toBeInTheDocument()
    expect(screen.getByText('Third')).toBeInTheDocument()

    act(() => {
      api!.success('Fourth', { duration: Infinity })
    })
    expect(screen.queryByText('First')).not.toBeInTheDocument()
    expect(screen.getByText('Second')).toBeInTheDocument()
    expect(screen.getByText('Third')).toBeInTheDocument()
    expect(screen.getByText('Fourth')).toBeInTheDocument()
  })

  it('dismiss removes the correct item', () => {
    let api: ReturnType<typeof useToast>
    renderWithToast(
      <ToastTrigger
        onMount={(a) => {
          api = a
        }}
      />,
    )
    let idA: string
    let idB: string
    act(() => {
      idA = api!.success('Alpha', { duration: Infinity })
      idB = api!.error('Beta', { duration: Infinity })
    })
    expect(screen.getByText('Alpha')).toBeInTheDocument()
    expect(screen.getByText('Beta')).toBeInTheDocument()

    act(() => {
      api!.dismiss(idA!)
    })
    act(() => {
      vi.advanceTimersByTime(200)
    })
    void idB
    expect(screen.getByText('Beta')).toBeInTheDocument()
  })

  it('dismiss button removes toast', () => {
    let api: ReturnType<typeof useToast>
    renderWithToast(
      <ToastTrigger
        onMount={(a) => {
          api = a
        }}
      />,
    )
    act(() => {
      api!.error('Oops', { duration: Infinity })
    })
    const dismissBtn = screen.getByRole('button', { name: 'Dismiss notification' })
    fireEvent.click(dismissBtn)
    act(() => {
      vi.runAllTimers()
    })
    expect(screen.queryByText('Oops')).not.toBeInTheDocument()
  })

  it('pauses auto-dismiss on mouseenter, resumes on mouseleave', () => {
    let api: ReturnType<typeof useToast>
    renderWithToast(
      <ToastTrigger
        onMount={(a) => {
          api = a
        }}
      />,
    )
    act(() => {
      api!.success('Hovered', { duration: 2000 })
    })
    const item = screen.getByRole('status')

    act(() => {
      fireEvent.mouseEnter(item)
      vi.advanceTimersByTime(3000)
    })
    expect(screen.getByText('Hovered')).toBeInTheDocument()

    act(() => {
      fireEvent.mouseLeave(item)
      vi.runAllTimers()
    })
    expect(screen.queryByText('Hovered')).not.toBeInTheDocument()
  })

})
