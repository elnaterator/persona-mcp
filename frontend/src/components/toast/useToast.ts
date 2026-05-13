import { useContext } from 'react'
import { ToastContext } from './toastContext'
import type { ToastApi } from './toastContext'

export function useToast(): ToastApi {
  const ctx = useContext(ToastContext)
  if (import.meta.env.DEV && !ctx) {
    throw new Error('useToast must be used within <ToastProvider>')
  }
  return ctx!
}
