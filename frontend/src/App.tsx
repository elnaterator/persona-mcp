import { useState } from 'react'
import Navigation from './components/Navigation'
import ResumeListView from './components/ResumeListView'
import ResumeDetailView from './components/ResumeDetailView'
import ApplicationListView from './components/ApplicationListView'
import ApplicationDetailView from './components/ApplicationDetailView'

type View =
  | { type: 'resume-list' }
  | { type: 'resume-detail'; id: number }
  | { type: 'app-list' }
  | { type: 'app-detail'; id: number }

function App() {
  const [view, setView] = useState<View>({ type: 'resume-list' })
  const activeNav = view.type.startsWith('resume') ? 'resumes' : 'applications'

  const handleNavigate = (section: 'resumes' | 'applications') => {
    if (section === 'resumes') {
      setView({ type: 'resume-list' })
    } else {
      setView({ type: 'app-list' })
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
      </main>
    </div>
  )
}

export default App
