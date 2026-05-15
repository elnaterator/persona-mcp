import type { FieldError as RHFFieldError } from 'react-hook-form'
import styles from './FieldError.module.css'

interface FieldErrorProps {
  error?: RHFFieldError
}

export function FieldError({ error }: FieldErrorProps) {
  if (!error?.message) return null
  return (
    <p role="alert" className={styles.fieldError}>
      {error.message}
    </p>
  )
}
