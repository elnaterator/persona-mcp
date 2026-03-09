import { useCallback, useEffect, useState } from 'react'
import { Link } from 'react-router'
import type { ResumeVersionSummary } from '../types/resume'
import { listResumes, createResume, deleteResume, setDefaultResume } from '../services/api'
import { LoadingSpinner } from './LoadingSpinner'
import { ConfirmDialog } from './ConfirmDialog'
import { StatusMessage } from './StatusMessage'
import styles from './ResumeListView.module.css'

export default function ResumeListView() {
  const [resumes, setResumes] = useState<ResumeVersionSummary[]>([])
  const [loading, setLoading] = useState(true)
  const [statusMessage, setStatusMessage] = useState<{ type: 'success' | 'error'; message: string } | null>(null)
  const [deleteTarget, setDeleteTarget] = useState<number | null>(null)

  const load = useCallback(async () => {
    try {
      setLoading(true)
      const data = await listResumes()
      setResumes(data)
    } catch {
      setStatusMessage({ type: 'error', message: 'Failed to load resume versions' })
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    load()
  }, [load])

  const handleCreate = async () => {
    const label = window.prompt('Enter a label for the new resume version:')
    if (!label || !label.trim()) return

    try {
      await createResume(label.trim())
      setStatusMessage({ type: 'success', message: 'Resume version created' })
      await load()
    } catch {
      setStatusMessage({ type: 'error', message: 'Failed to create resume version' })
    }
  }

  const handleSetDefault = async (id: number) => {
    try {
      await setDefaultResume(id)
      setStatusMessage({ type: 'success', message: 'Default resume updated' })
      await load()
    } catch {
      setStatusMessage({ type: 'error', message: 'Failed to set default resume' })
    }
  }

  const handleDeleteClick = (id: number) => {
    setDeleteTarget(id)
  }

  const handleDeleteConfirm = async () => {
    if (deleteTarget === null) return
    try {
      await deleteResume(deleteTarget)
      setStatusMessage({ type: 'success', message: 'Resume version deleted' })
      setDeleteTarget(null)
      await load()
    } catch {
      setStatusMessage({ type: 'error', message: 'Failed to delete resume version' })
      setDeleteTarget(null)
    }
  }

  const formatDate = (iso: string) => {
    return new Date(iso).toLocaleDateString(undefined, {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    })
  }

  if (loading) return <LoadingSpinner />

  return (
    <div className={styles.container} data-testid="resume-list-view">
      <div className={styles.header}>
        <h2 className={styles.heading}>Resume Versions</h2>
        <button className={styles.newButton} onClick={handleCreate}>
          New Version
        </button>
      </div>

      {statusMessage && (
        <StatusMessage
          type={statusMessage.type}
          message={statusMessage.message}
          onDismiss={() => setStatusMessage(null)}
        />
      )}

      {resumes.length === 0 ? (
        <p className={styles.empty}>No resume versions found.</p>
      ) : (
        <ul className={styles.list}>
          {resumes.map((resume) => (
            <li key={resume.id} className={styles.item}>
              <Link to={`/resumes/${resume.id}`} className={styles.itemLink}>
                <div className={styles.itemMain}>
                  <span className={styles.label}>{resume.label}</span>
                  {resume.is_default && (
                    <span className={styles.defaultBadge}>Default</span>
                  )}
                </div>
                <div className={styles.itemMeta}>
                  <span className={styles.metaItem}>
                    {resume.app_count} application{resume.app_count !== 1 ? 's' : ''}
                  </span>
                  <span className={styles.metaItem}>
                    Created {formatDate(resume.created_at)}
                  </span>
                </div>
              </Link>
              <div className={styles.itemActions}>
                {!resume.is_default && (
                  <button
                    className={styles.actionButton}
                    onClick={() => handleSetDefault(resume.id)}
                  >
                    Set as Default
                  </button>
                )}
                <button
                  className={`${styles.actionButton} ${styles.deleteButton}`}
                  onClick={() => handleDeleteClick(resume.id)}
                  disabled={resumes.length === 1}
                  title={resumes.length === 1 ? 'Cannot delete the only version' : undefined}
                >
                  Delete
                </button>
              </div>
            </li>
          ))}
        </ul>
      )}

      {deleteTarget !== null && (
        <ConfirmDialog
          message="Are you sure you want to delete this resume version? This cannot be undone."
          onConfirm={handleDeleteConfirm}
          onCancel={() => setDeleteTarget(null)}
        />
      )}
    </div>
  )
}
