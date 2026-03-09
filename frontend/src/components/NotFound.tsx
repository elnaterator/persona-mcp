import { Link } from 'react-router'
import styles from './NotFound.module.css'

interface NotFoundProps {
  entityName: string
  backTo: string
  backLabel: string
}

export default function NotFound({ entityName, backTo, backLabel }: NotFoundProps) {
  return (
    <div className={styles.container} data-testid="not-found">
      <h2 className={styles.heading}>{entityName} not found</h2>
      <p className={styles.message}>
        The {entityName.toLowerCase()} you're looking for doesn't exist or may have been deleted.
      </p>
      <Link to={backTo} className={styles.backLink}>
        {backLabel}
      </Link>
    </div>
  )
}
