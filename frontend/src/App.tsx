import { useState } from 'react'
import Navigation from './components/Navigation'
import ResumeListView from './components/ResumeListView'
import ResumeDetailView from './components/ResumeDetailView'
import ApplicationListView from './components/ApplicationListView'
import ApplicationDetailView from './components/ApplicationDetailView'
import AccomplishmentListView from './components/AccomplishmentListView'
import AccomplishmentDetailView from './components/AccomplishmentDetailView'

type View =
  | { type: 'resume-list' }
  | { type: 'resume-detail'; id: number }
  | { type: 'app-list' }
  | { type: 'app-detail'; id: number }
  | { type: 'acc-list' }
  | { type: 'acc-detail'; id: number }

type NavSection = 'resumes' | 'applications' | 'accomplishments'

function App() {
  const [view, setView] = useState<View>({ type: 'resume-list' })

  const activeNav: NavSection = view.type.startsWith('resume')
    ? 'resumes'
    : view.type.startsWith('app')
      ? 'applications'
      : 'accomplishments'

  const handleNavigate = (section: NavSection) => {
    if (section === 'resumes') {
      setView({ type: 'resume-list' })
    } else if (section === 'applications') {
      setView({ type: 'app-list' })
    } else {
      setView({ type: 'acc-list' })
    }
  }

  return (
    <div className="app">
      <header className="app-header">
        <div className="app-header-inner">
          <h1>Persona</h1>
          <Navigation activeView={activeNav} onNavigate={handleNavigate} />
        </div>
      </header>
      <main>
        {view.type === 'resume-list' && (
          <ResumeListView onSelectResume={(id) => setView({ type: 'resume-detail', id })} />
        )}
        {view.type === 'resume-detail' && (
          <ResumeDetailView
            versionId={view.id}
            onBack={() => setView({ type: 'resume-list' })}
          />
        )}
        {view.type === 'app-list' && (
          <ApplicationListView onSelectApp={(id) => setView({ type: 'app-detail', id })} />
        )}
        {view.type === 'app-detail' && (
          <ApplicationDetailView
            appId={view.id}
            onBack={() => setView({ type: 'app-list' })}
          />
        )}
        {view.type === 'acc-list' && (
          <AccomplishmentListView
            onSelectAccomplishment={(id) => setView({ type: 'acc-detail', id })}
          />
        )}
        {view.type === 'acc-detail' && (
          <AccomplishmentDetailView
            accomplishmentId={view.id}
            onBack={() => setView({ type: 'acc-list' })}
          />
        )}
      </main>
    </div>
  )
}

export default App
