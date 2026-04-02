import { useCallback, useEffect, useState } from 'react'
import { useParams, useNavigate, Link } from 'react-router'
import type { ResumeVersion } from '../types/resume'
import { getResumeVersion, updateResumeLabel } from '../services/api'
import ContactSection from './ContactSection'
import SummarySection from './SummarySection'
import ExperienceSection from './ExperienceSection'
import EducationSection from './EducationSection'
import SkillsSection from './SkillsSection'
import Breadcrumb from './Breadcrumb'
import NotFound from './NotFound'
import { LoadingSpinner } from './LoadingSpinner'
import { StatusMessage } from './StatusMessage'
import styles from './ResumeDetailView.module.css'

export default function ResumeDetailView() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()

  const numericId = id && /^\d+$/.test(id) ? Number(id) : null

  const [version, setVersion] = useState<ResumeVersion | null>(null)
  const [notFound, setNotFound] = useState(false)
  const [forbidden, setForbidden] = useState(false)
  const [loading, setLoading] = useState(true)
  const [statusMessage, setStatusMessage] = useState<{ type: 'success' | 'error'; message: string } | null>(null)
  const [editingLabel, setEditingLabel] = useState(false)
  const [labelInput, setLabelInput] = useState('')

  useEffect(() => {
    if (numericId === null) {
      navigate('/resumes', { replace: true })
    }
  }, [numericId, navigate])

  const load = useCallback(async () => {
    if (numericId === null) return
    try {
      setLoading(true)
      const data = await getResumeVersion(numericId)
      setVersion(data)
      setLabelInput(data.label)
    } catch (err: unknown) {
      const status = (err as { status?: number })?.status
      if (status === 404) {
        setNotFound(true)
      } else if (status === 403) {
        setForbidden(true)
      } else {
        setStatusMessage({ type: 'error', message: 'Failed to load resume version' })
      }
    } finally {
      setLoading(false)
    }
  }, [numericId])

  useEffect(() => {
    load()
  }, [load])

  const handleLabelSave = async () => {
    if (!labelInput.trim() || numericId === null) return
    try {
      const updated = await updateResumeLabel(numericId, labelInput.trim())
      setVersion((prev) => prev ? { ...prev, label: updated.label } : prev)
      setEditingLabel(false)
    } catch {
      setStatusMessage({ type: 'error', message: 'Failed to update label' })
    }
  }

  if (numericId === null) return null
  if (loading) return <LoadingSpinner />
  if (notFound) return <NotFound entityName="Resume" backTo="/resumes" backLabel="Back to Resumes" />
  if (forbidden) return <NotFound entityName="Resume" backTo="/resumes" backLabel="Back to Resumes" heading="This resume isn't yours" message="This resume belongs to another account and cannot be accessed." />
  if (!version) return null

  const resume = version.resume_data

  return (
    <div className={styles.container} data-testid="resume-detail-view">
      <Breadcrumb
        items={[
          { label: 'Resumes', to: '/resumes' },
          { label: version.label },
        ]}
      />

      <div className={styles.topBar}>
        <Link to="/resumes" className={styles.backButton}>
          Back to list
        </Link>
        {version.is_default && (
          <span className={styles.defaultBadge}>Default</span>
        )}
      </div>

      <div className={styles.labelRow}>
        {editingLabel ? (
          <div className={styles.labelEdit}>
            <input
              className={styles.labelInput}
              value={labelInput}
              onChange={(e) => setLabelInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter') handleLabelSave()
                if (e.key === 'Escape') setEditingLabel(false)
              }}
              autoFocus
            />
            <button className={styles.saveLabel} onClick={handleLabelSave}>
              Save
            </button>
            <button className={styles.cancelLabel} onClick={() => setEditingLabel(false)}>
              Cancel
            </button>
          </div>
        ) : (
          <div className={styles.labelDisplay}>
            <h2 className={styles.label}>{version.label}</h2>
            <button className={styles.editLabelBtn} onClick={() => setEditingLabel(true)}>
              Rename
            </button>
          </div>
        )}
      </div>

      {statusMessage && (
        <StatusMessage
          type={statusMessage.type}
          message={statusMessage.message}
          onDismiss={() => setStatusMessage(null)}
        />
      )}

      <div className={styles.document}>
        <ContactSection
          contact={resume.contact}
          onUpdate={load}
          versionId={numericId}
        />
        <SummarySection
          summary={resume.summary}
          onUpdate={load}
          versionId={numericId}
        />
        <ExperienceSection
          experience={resume.experience}
          onUpdate={load}
          versionId={numericId}
        />
        <EducationSection
          education={resume.education}
          onUpdate={load}
          versionId={numericId}
        />
        <SkillsSection
          skills={resume.skills}
          onUpdate={load}
          versionId={numericId}
        />
      </div>
    </div>
  )
}
