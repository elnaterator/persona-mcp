import { useCallback, useEffect, useRef, useState } from 'react'
import type { Toast } from './toastContext'
import styles from './Toast.module.css'

interface ToastItemProps {
  toast: Toast
  onDismiss: (id: string) => void
}

type AnimState = 'entering' | 'visible' | 'leaving'

export function ToastItem({ toast, onDismiss }: ToastItemProps) {
  const [animState, setAnimState] = useState<AnimState>('entering')
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const isPersistent = toast.duration === Infinity

  const startLeave = useCallback(() => {
    setAnimState('leaving')
    setTimeout(() => onDismiss(toast.id), 150)
  }, [toast.id, onDismiss])

  const startTimer = useCallback(() => {
    if (isPersistent) return
    timerRef.current = setTimeout(startLeave, toast.duration)
  }, [isPersistent, toast.duration, startLeave])

  const clearTimer = useCallback(() => {
    if (timerRef.current) {
      clearTimeout(timerRef.current)
      timerRef.current = null
    }
  }, [])

  useEffect(() => {
    const enterTimer = setTimeout(() => setAnimState('visible'), 10)
    startTimer()
    return () => {
      clearTimeout(enterTimer)
      clearTimer()
    }
  }, [startTimer, clearTimer])

  const handleDismiss = () => {
    clearTimer()
    startLeave()
  }

  const handleMouseEnter = () => clearTimer()
  const handleMouseLeave = () => startTimer()
  const handleFocus = () => clearTimer()
  const handleBlur = () => startTimer()

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Escape') handleDismiss()
  }

  const isError = toast.type === 'error'
  const role = isError ? 'alert' : 'status'
  const ariaLive = isError ? 'assertive' : 'polite'

  return (
    <li
      className={`${styles.item} ${styles[toast.type]}`}
      data-state={animState}
      role={role}
      aria-live={ariaLive}
      aria-atomic="true"
      tabIndex={isPersistent ? 0 : -1}
      onMouseEnter={handleMouseEnter}
      onMouseLeave={handleMouseLeave}
      onFocus={handleFocus}
      onBlur={handleBlur}
      onKeyDown={handleKeyDown}
    >
      <span className={styles.message}>{toast.message}</span>
      {toast.action && (
        <button
          className={styles.actionButton}
          onClick={() => {
            toast.action!.onClick()
            handleDismiss()
          }}
        >
          {toast.action.label}
        </button>
      )}
      <button
        className={styles.dismissButton}
        onClick={handleDismiss}
        aria-label="Dismiss notification"
      >
        ×
      </button>
    </li>
  )
}
