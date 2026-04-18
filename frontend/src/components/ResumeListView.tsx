import { useCallback, useEffect, useState } from 'react'
import { Link } from 'react-router'
import type { ResumeVersionSummary } from '../types/resume'
import { listResumes, createResume } from '../services/api'
import { LoadingSpinner } from './LoadingSpinner'
import { StatusMessage } from './StatusMessage'
import { InlineCreateForm } from './InlineCreateForm'
import styles from './ResumeListView.module.css'

export default function ResumeListView() {
  const [resumes, setResumes] = useState<ResumeVersionSummary[]>([])
  const [loading, setLoading] = useState(true)
  const [statusMessage, setStatusMessage] = useState<{ type: 'success' | 'error'; message: string } | null>(null)
  const [creating, setCreating] = useState(false)

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

  const handleCreateConfirm = async (label: string) => {
    await createResume(label)
    setStatusMessage({ type: 'success', message: 'Resume version created' })
    setCreating(false)
    await load()
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
        <button className={styles.newButton} onClick={() => setCreating(true)}>
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

      {creating && (
        <InlineCreateForm
          onConfirm={handleCreateConfirm}
          onCancel={() => setCreating(false)}
          placeholder="e.g. Senior Engineer, Remote-focused..."
          confirmLabel="Create"
        />
      )}

      {resumes.length === 0 ? (
        <p className={styles.empty}>No resume versions found.</p>
      ) : (
        <ul className={styles.list}>
          {[...resumes].sort((a, b) => (b.is_default ? 1 : 0) - (a.is_default ? 1 : 0)).map((resume) => (
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
            </li>
          ))}
        </ul>
      )}

    </div>
  )
}
