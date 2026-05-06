import { useState, useCallback, useRef } from 'react'

export interface StatusMessageState {
  message: string | null
  isError: boolean
  showMessage: (msg: string, error?: boolean, autoDismissMs?: number) => void
  clearMessage: () => void
}

export function useStatusMessage(): StatusMessageState {
  const [message, setMessage] = useState<string | null>(null)
  const [isError, setIsError] = useState(false)
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  const clearMessage = useCallback(() => {
    if (timerRef.current) clearTimeout(timerRef.current)
    setMessage(null)
    setIsError(false)
  }, [])

  const showMessage = useCallback((msg: string, error = false, autoDismissMs = 3000) => {
    if (timerRef.current) clearTimeout(timerRef.current)
    setMessage(msg)
    setIsError(error)
    if (autoDismissMs > 0) {
      timerRef.current = setTimeout(clearMessage, autoDismissMs)
    }
  }, [clearMessage])

  return { message, isError, showMessage, clearMessage }
}
