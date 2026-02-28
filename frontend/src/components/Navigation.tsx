import styles from './Navigation.module.css'

type NavSection = 'resumes' | 'applications' | 'accomplishments' | 'connect'

interface NavigationProps {
  activeView: NavSection
  onNavigate: (view: NavSection) => void
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
      <button
        className={`${styles.navItem} ${activeView === 'accomplishments' ? styles.active : ''}`}
        onClick={() => onNavigate('accomplishments')}
        aria-current={activeView === 'accomplishments' ? 'page' : undefined}
      >
        Accomplishments
      </button>
      <button
        className={`${styles.navItem} ${activeView === 'connect' ? styles.active : ''}`}
        onClick={() => onNavigate('connect')}
        aria-current={activeView === 'connect' ? 'page' : undefined}
      >
        Connect
      </button>
    </nav>
  )
}
