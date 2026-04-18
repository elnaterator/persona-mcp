import { useCallback, useEffect, useState } from 'react'
import { useParams, useNavigate, Link } from 'react-router'
import { Trash2, Pencil, Check, X } from 'lucide-react'
import type { ResumeVersion } from '../types/resume'
import { getResumeVersion, updateResumeLabel, deleteResume, setDefaultResume } from '../services/api'
import ContactSection from './ContactSection'
import SummarySection from './SummarySection'
import ExperienceSection from './ExperienceSection'
import EducationSection from './EducationSection'
import SkillsSection from './SkillsSection'
import Breadcrumb from './Breadcrumb'
import NotFound from './NotFound'
import { LoadingSpinner } from './LoadingSpinner'
import { StatusMessage } from './StatusMessage'
import { ConfirmDialog } from './ConfirmDialog'
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
  const [confirmDelete, setConfirmDelete] = useState(false)
  const [deleting, setDeleting] = useState(false)

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

  const handleDelete = async () => {
    if (numericId === null) return
    setDeleting(true)
    try {
      await deleteResume(numericId)
      navigate('/resumes')
    } catch {
      setDeleting(false)
      setConfirmDelete(false)
      setStatusMessage({ type: 'error', message: 'Failed to delete resume version' })
    }
  }

  const handleSetDefault = async () => {
    if (numericId === null) return
    try {
      await setDefaultResume(numericId)
      await load()
      setStatusMessage({ type: 'success', message: 'Default resume updated' })
    } catch {
      setStatusMessage({ type: 'error', message: 'Failed to set default resume' })
    }
  }

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
        <div className={styles.topBarActions}>
          {!version.is_default && (
            <button className={styles.setDefaultButton} onClick={handleSetDefault}>
              Set as Default
            </button>
          )}
          <button
            className={styles.deleteButton}
            onClick={() => setConfirmDelete(true)}
            aria-label="Delete resume version"
          >
            <Trash2 size={14} />
          </button>
        </div>
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
            <button className={`${styles.iconBtn} ${styles.saveIcon}`} onClick={handleLabelSave} aria-label="Save label">
              <Check size={14} />
            </button>
            <button className={`${styles.iconBtn} ${styles.cancelIcon}`} onClick={() => setEditingLabel(false)} aria-label="Cancel editing">
              <X size={14} />
            </button>
          </div>
        ) : (
          <div className={styles.labelDisplay}>
            <h2 className={styles.label}>{version.label}</h2>
            <button className={styles.iconBtn} onClick={() => setEditingLabel(true)} aria-label="Edit label">
              <Pencil size={14} />
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

      {confirmDelete && (
        <ConfirmDialog
          message="Delete this resume version? This cannot be undone."
          onConfirm={handleDelete}
          onCancel={() => setConfirmDelete(false)}
        />
      )}
    </div>
  )
}
