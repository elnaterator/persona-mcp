import { useEffect, useState } from 'react'
import { Link } from 'react-router'
import { Link2 } from 'lucide-react'
import { useResumeList, useResumeMutations } from '../../hooks/queries'
import { LoadingSpinner } from '../../components/LoadingSpinner'
import { InlineCreateForm } from '../../components/InlineCreateForm'
import { useToast } from '../../components/toast'
import styles from './ResumeListView.module.css'

export default function ResumeListView() {
  const { data: resumes = [], isPending, isError } = useResumeList()
  const { create } = useResumeMutations()
  const { success, error } = useToast()
  const [creating, setCreating] = useState(false)

  useEffect(() => {
    if (isError) {
      error('Failed to load resume versions')
    }
  }, [isError, error])

  const handleCreateConfirm = async (label: string) => {
    try {
      await create.mutateAsync(label)
      success('Resume version created')
      setCreating(false)
    } catch {
      error('Failed to create resume version')
    }
  }

  const formatDate = (iso: string) => {
    return new Date(iso).toLocaleDateString(undefined, {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    })
  }

  if (isPending) return <LoadingSpinner />

  return (
    <div className={styles.container} data-testid="resume-list-view">
      <div className={styles.header}>
        <h2 className={styles.heading}>Resume Versions</h2>
        <button className={styles.newButton} onClick={() => setCreating(true)}>
          New Version
        </button>
      </div>

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
                {resume.tags && resume.tags.length > 0 && (
                  <div className={styles.tagList}>
                    {resume.tags.map((tag) => (
                      <span key={tag} className={styles.tagBadge}>{tag}</span>
                    ))}
                  </div>
                )}
                <div className={styles.itemMeta}>
                  <span className={styles.metaItem}>
                    {resume.app_count} application{resume.app_count !== 1 ? 's' : ''}
                  </span>
                  {!!resume.link_count && (
                    <span className={`${styles.metaItem} ${styles.linkCount}`}><Link2 size={11} />{resume.link_count}</span>
                  )}
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
