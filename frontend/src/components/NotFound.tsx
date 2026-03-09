import { Link } from 'react-router'
import styles from './NotFound.module.css'

interface NotFoundProps {
  entityName: string
  backTo: string
  backLabel: string
  heading?: string
  message?: string
}

export default function NotFound({ entityName, backTo, backLabel, heading, message }: NotFoundProps) {
  return (
    <div className={styles.container} data-testid="not-found">
      <h2 className={styles.heading}>{heading ?? `${entityName} not found`}</h2>
      <p className={styles.message}>
        {message ?? `The ${entityName.toLowerCase()} you're looking for doesn't exist or may have been deleted.`}
      </p>
      <Link to={backTo} className={styles.backLink}>
        {backLabel}
      </Link>
    </div>
  )
}
