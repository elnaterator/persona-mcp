import type { ReactNode } from 'react'
import styles from './DetailLayout.module.css'

interface DetailLayoutProps {
  children: ReactNode
  sidebar: ReactNode
}

export default function DetailLayout({ children, sidebar }: DetailLayoutProps) {
  return (
    <div className={styles.layout}>
      <div className={styles.main}>{children}</div>
      <aside className={styles.sidebar}>{sidebar}</aside>
    </div>
  )
}
