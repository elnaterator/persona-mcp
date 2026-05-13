import { useCallback, useMemo, useState } from 'react'
import { ToastContext } from './toastContext'
import type { Toast, ToastApi, ToastInput, ToastType } from './toastContext'
import { ToastContainer } from './ToastContainer'

function defaultDuration(type: ToastType): number {
  if (type === 'error') return 3000
  return 1500
}

interface ToastProviderProps {
  children: React.ReactNode
  max?: number
}

export function ToastProvider({ children, max = 3 }: ToastProviderProps) {
  const [toasts, setToasts] = useState<Toast[]>([])

  const dismiss = useCallback((id: string) => {
    setToasts((q) => q.filter((t) => t.id !== id))
  }, [])

  const toast = useCallback(
    (input: ToastInput): string => {
      const id = input.id ?? crypto.randomUUID()
      setToasts((q) => {
        const existingIdx = q.findIndex((t) => t.id === id)
        const next: Toast = {
          id,
          createdAt: Date.now(),
          duration: input.duration ?? defaultDuration(input.type),
          type: input.type,
          message: input.message,
          action: input.action,
        }
        if (existingIdx >= 0) {
          const copy = [...q]
          copy[existingIdx] = next
          return copy
        }
        const trimmed = q.length >= max ? q.slice(1) : q
        return [...trimmed, next]
      })
      return id
    },
    [max],
  )

  const api = useMemo<ToastApi>(
    () => ({
      toast,
      success: (m, o) => toast({ type: 'success', message: m, ...o }),
      error: (m, o) => toast({ type: 'error', message: m, ...o }),
      warning: (m, o) => toast({ type: 'warning', message: m, ...o }),
      dismiss,
      dismissAll: () => setToasts([]),
    }),
    [toast, dismiss],
  )

  return (
    <ToastContext.Provider value={api}>
      {children}
      <ToastContainer toasts={toasts} onDismiss={dismiss} />
    </ToastContext.Provider>
  )
}
