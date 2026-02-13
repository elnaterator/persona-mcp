import { useEffect } from 'react'
import styles from './StatusMessage.module.css'

interface StatusMessageProps {
  type: 'success' | 'error'
  message: string
  onDismiss?: () => void
  autoHideDuration?: number
}

export function StatusMessage({
  type,
  message,
  onDismiss,
  autoHideDuration = 3000,
}: StatusMessageProps) {
  useEffect(() => {
    if (type === 'success' && onDismiss && autoHideDuration > 0) {
      const timer = setTimeout(onDismiss, autoHideDuration)
      return () => clearTimeout(timer)
    }
  }, [type, onDismiss, autoHideDuration])

  return (
    <div className={`${styles.message} ${styles[type]}`} role="alert">
      <span className={styles.text}>{message}</span>
      {onDismiss && (
        <button
          className={styles.dismissButton}
          onClick={onDismiss}
          aria-label="Dismiss message"
        >
          ×
        </button>
      )}
    </div>
  )
}
