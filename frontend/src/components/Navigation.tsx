import { NavLink } from 'react-router'
import { Terminal, FileText, Briefcase, Trophy, StickyNote } from 'lucide-react'
import styles from './Navigation.module.css'

function navClass({ isActive }: { isActive: boolean }) {
  return `${styles.navItem}${isActive ? ` ${styles.active}` : ''}`
}

function connectClass({ isActive }: { isActive: boolean }) {
  return `${styles.navItem} ${styles.connectItem}${isActive ? ` ${styles.active}` : ''}`
}

export default function Navigation() {
  return (
    <nav className={styles.nav} aria-label="Main navigation">
      <NavLink to="/connect" className={connectClass}>
        <Terminal size={16} />
        Connect
      </NavLink>
      <NavLink to="/resumes" className={navClass} end={false}>
        <FileText size={16} />
        Resumes
      </NavLink>
      <NavLink to="/applications" className={navClass} end={false}>
        <Briefcase size={16} />
        Applications
      </NavLink>
      <NavLink to="/accomplishments" className={navClass} end={false}>
        <Trophy size={16} />
        Accomplishments
      </NavLink>
      <NavLink to="/notes" className={navClass} end={false}>
        <StickyNote size={16} />
        Notes
      </NavLink>
    </nav>
  )
}
