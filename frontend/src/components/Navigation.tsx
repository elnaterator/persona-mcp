import styles from './Navigation.module.css'

interface NavigationProps {
  activeView: 'resumes' | 'applications'
  onNavigate: (view: 'resumes' | 'applications') => void
}

export default function Navigation({ activeView, onNavigate }: NavigationProps) {
  return (
    <nav className={styles.nav} aria-label="Main navigation">
      <button
        className={`${styles.navItem} ${activeView === 'resumes' ? styles.active : ''}`}
        onClick={() => onNavigate('resumes')}
        aria-current={activeView === 'resumes' ? 'page' : undefined}
      >
        Resumes
      </button>
      <button
        className={`${styles.navItem} ${activeView === 'applications' ? styles.active : ''}`}
        onClick={() => onNavigate('applications')}
        aria-current={activeView === 'applications' ? 'page' : undefined}
      >
        Applications
      </button>
    </nav>
  )
}
