import { createContext } from 'react'

export type ToastType = 'success' | 'error' | 'warning'

export interface Toast {
  id: string
  type: ToastType
  message: string
  duration: number
  action?: { label: string; onClick: () => void }
  createdAt: number
}

export interface ToastInput {
  type: ToastType
  message: string
  id?: string
  duration?: number
  action?: { label: string; onClick: () => void }
}

export interface ToastOptions {
  id?: string
  duration?: number
  action?: { label: string; onClick: () => void }
}

export interface ToastApi {
  toast: (input: ToastInput) => string
  success: (message: string, opts?: ToastOptions) => string
  error: (message: string, opts?: ToastOptions) => string
  warning: (message: string, opts?: ToastOptions) => string
  dismiss: (id: string) => void
  dismissAll: () => void
}

export const ToastContext = createContext<ToastApi | null>(null)
