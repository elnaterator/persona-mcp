import { Navigate, Route, Routes } from 'react-router'
import ResumeListView from './components/ResumeListView'
import ResumeDetailView from './components/ResumeDetailView'
import ApplicationListView from './components/ApplicationListView'
import ApplicationDetailView from './components/ApplicationDetailView'
import AccomplishmentListView from './components/AccomplishmentListView'
import AccomplishmentDetailView from './components/AccomplishmentDetailView'
import ConnectView from './components/ConnectView'

export default function AppRoutes() {
  return (
    <Routes>
      <Route path="/" element={<Navigate to="/resumes" replace />} />
      <Route path="/resumes" element={<ResumeListView />} />
      <Route path="/resumes/:id" element={<ResumeDetailView />} />
      <Route path="/applications" element={<ApplicationListView />} />
      <Route path="/applications/:id" element={<ApplicationDetailView />} />
      <Route path="/accomplishments" element={<AccomplishmentListView />} />
      <Route path="/accomplishments/:id" element={<AccomplishmentDetailView />} />
      <Route path="/connect" element={<ConnectView />} />
      <Route path="*" element={<Navigate to="/resumes" replace />} />
    </Routes>
  )
}
