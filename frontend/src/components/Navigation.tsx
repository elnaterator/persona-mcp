import { NavLink } from 'react-router'
import styles from './Navigation.module.css'

function navClass({ isActive }: { isActive: boolean }) {
  return `${styles.navItem}${isActive ? ` ${styles.active}` : ''}`
}

export default function Navigation() {
  return (
    <nav className={styles.nav} aria-label="Main navigation">
      <NavLink to="/resumes" className={navClass} end={false}>
        Resumes
      </NavLink>
      <NavLink to="/applications" className={navClass} end={false}>
        Applications
      </NavLink>
      <NavLink to="/accomplishments" className={navClass} end={false}>
        Accomplishments
      </NavLink>
      <NavLink to="/notes" className={navClass} end={false}>
        Notes
      </NavLink>
      <NavLink to="/connect" className={navClass}>
        Connect
      </NavLink>
    </nav>
  )
}
