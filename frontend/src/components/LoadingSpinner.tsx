import styles from './LoadingSpinner.module.css'

export function LoadingSpinner() {
  return (
    <div className={styles.container} data-testid="loading-spinner">
      <div className={styles.spinner} aria-label="Loading..." role="status">
        <span className={styles.srOnly}>Loading...</span>
      </div>
    </div>
  )
}
