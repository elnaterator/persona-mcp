import { Link } from 'react-router'
import styles from './Breadcrumb.module.css'

interface BreadcrumbItem {
  label: string
  to?: string
}

interface BreadcrumbProps {
  items: BreadcrumbItem[]
}

export default function Breadcrumb({ items }: BreadcrumbProps) {
  if (items.length === 0) return null

  return (
    <nav className={styles.breadcrumb} aria-label="Breadcrumb">
      {items.map((item, index) => {
        const isLast = index === items.length - 1
        return (
          <span key={index} className={styles.segment}>
            {index > 0 && <span className={styles.separator}>&gt;</span>}
            {isLast || !item.to ? (
              <span className={styles.current}>{item.label}</span>
            ) : (
              <Link to={item.to} className={styles.link}>
                {item.label}
              </Link>
            )}
          </span>
        )
      })}
    </nav>
  )
}
