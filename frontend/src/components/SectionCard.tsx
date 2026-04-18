import { ReactNode } from 'react'
import styles from './SectionCard.module.css'

interface SectionCardProps {
  label?: string
  action?: ReactNode
  children: ReactNode
}

export function SectionCard({ label, action, children }: SectionCardProps) {
  return (
    <div className={styles.section}>
      {(label || action) && (
        <div className={styles.header}>
          {label && <h3 className={styles.label}>{label}</h3>}
          {action}
        </div>
      )}
      {children}
    </div>
  )
}
