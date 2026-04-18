import { useState, useEffect } from 'react'
import { useParams, useNavigate, Link } from 'react-router'
import { Pencil, Trash2, Check, X } from 'lucide-react'
import type { Accomplishment } from '../types/resume'
import { getAccomplishment, updateAccomplishment, deleteAccomplishment } from '../services/api'
import Breadcrumb from './Breadcrumb'
import NotFound from './NotFound'
import { ConfirmDialog } from './ConfirmDialog'
import { StatusMessage } from './StatusMessage'
import { SectionCard } from './SectionCard'
import { MarkdownContent } from './MarkdownContent'
import styles from './AccomplishmentDetailView.module.css'

export default function AccomplishmentDetailView() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()

  const numericId = id && /^\d+$/.test(id) ? Number(id) : null

  const [acc, setAcc] = useState<Accomplishment | null>(null)
  const [notFound, setNotFound] = useState(false)
  const [forbidden, setForbidden] = useState(false)
  const [editing, setEditing] = useState(false)
  const [editForm, setEditForm] = useState<Partial<Accomplishment>>({})
  const [editError, setEditError] = useState('')
  const [saving, setSaving] = useState(false)
  const [confirmDelete, setConfirmDelete] = useState(false)
  const [, setDeleting] = useState(false)
  const [statusMessage, setStatusMessage] = useState<{ type: 'success' | 'error'; message: string } | null>(null)

  useEffect(() => {
    if (numericId === null) {
      navigate('/accomplishments', { replace: true })
      return
    }
    getAccomplishment(numericId).then(setAcc).catch((err: unknown) => {
      const status = (err as { status?: number })?.status
      if (status === 404) {
        setNotFound(true)
      } else if (status === 403) {
        setForbidden(true)
      }
    })
  }, [numericId, navigate])

  if (numericId === null) return null
  if (notFound) return <NotFound entityName="Accomplishment" backTo="/accomplishments" backLabel="Back to Accomplishments" />
  if (forbidden) return <NotFound entityName="Accomplishment" backTo="/accomplishments" backLabel="Back to Accomplishments" heading="This accomplishment isn't yours" message="This accomplishment belongs to another account and cannot be accessed." />
  if (!acc) {
    return <div>Loading…</div>
  }

  const startEdit = () => {
    setEditForm({
      title: acc.title,
      situation: acc.situation,
      task: acc.task,
      action: acc.action,
      result: acc.result,
      accomplishment_date: acc.accomplishment_date ?? '',
      tags: acc.tags,
    })
    setEditError('')
    setEditing(true)
  }

  const handleEditFieldChange = (field: keyof Accomplishment, value: string | string[]) => {
    setEditForm((prev) => ({ ...prev, [field]: value }))
  }

  const handleSave = async () => {
    if (!editForm.title?.trim()) {
      setEditError('Title is required')
      return
    }
    setSaving(true)
    setEditError('')
    try {
      const updated = await updateAccomplishment(numericId, {
        ...editForm,
        accomplishment_date: editForm.accomplishment_date || null,
        tags: editForm.tags as string[],
      })
      setAcc(updated)
      setEditing(false)
      setStatusMessage({ type: 'success', message: 'Saved' })
    } catch (err) {
      setEditError(err instanceof Error ? err.message : 'Failed to save')
    } finally {
      setSaving(false)
    }
  }

  const handleDelete = async () => {
    setDeleting(true)
    try {
      await deleteAccomplishment(numericId)
      navigate('/accomplishments')
    } catch {
      setDeleting(false)
      setConfirmDelete(false)
      setStatusMessage({ type: 'error', message: 'Failed to delete accomplishment' })
    }
  }

  const STAR_FIELDS: { key: keyof Accomplishment; label: string; placeholder: string }[] = [
    { key: 'situation', label: 'Situation', placeholder: 'Describe the context or background…' },
    { key: 'task', label: 'Task', placeholder: 'What was your specific responsibility or goal?' },
    { key: 'action', label: 'Action', placeholder: 'What steps did you take to address the situation?' },
    { key: 'result', label: 'Result', placeholder: 'What was the outcome or impact? Include metrics where possible.' },
  ]

  return (
    <div className={styles.container}>
      <Breadcrumb
        items={[
          { label: 'Accomplishments', to: '/accomplishments' },
          { label: acc.title },
        ]}
      />

      <div className={styles.topBar}>
        <Link to="/accomplishments" className={styles.backButton}>Back</Link>
        {editing ? (
          <input
            className={styles.titleInput}
            type="text"
            value={editForm.title ?? ''}
            onChange={(e) => handleEditFieldChange('title', e.target.value)}
            autoFocus
          />
        ) : (
          <h2 className={styles.topBarTitle}>{acc.title}</h2>
        )}
        <div className={styles.topBarActions}>
          {editing ? (
            <>
              <button
                className={styles.saveIconButton}
                onClick={handleSave}
                disabled={saving}
                aria-label="Save accomplishment"
              >
                <Check size={14} />
              </button>
              <button
                className={styles.cancelIconButton}
                onClick={() => setEditing(false)}
                aria-label="Cancel editing"
              >
                <X size={14} />
              </button>
            </>
          ) : (
            <>
              <button className={styles.editButton} onClick={startEdit} aria-label="Edit accomplishment">
                <Pencil size={14} />
              </button>
              <button className={styles.deleteButton} onClick={() => setConfirmDelete(true)} aria-label="Delete accomplishment">
                <Trash2 size={14} />
              </button>
            </>
          )}
        </div>
      </div>

      {editError && <p className={styles.formError}>{editError}</p>}

      {statusMessage && (
        <StatusMessage
          type={statusMessage.type}
          message={statusMessage.message}
          onDismiss={() => setStatusMessage(null)}
        />
      )}

      {editing ? (
        <div className={styles.metaEdit}>
          <div className={styles.metaField}>
            <label className={styles.metaLabel} htmlFor="edit-date">Date</label>
            <input
              id="edit-date"
              className={styles.metaInput}
              type="date"
              value={(editForm.accomplishment_date as string) ?? ''}
              onChange={(e) => handleEditFieldChange('accomplishment_date', e.target.value)}
            />
          </div>
          <div className={styles.metaField}>
            <label className={styles.metaLabel} htmlFor="edit-tags">Tags</label>
            <input
              id="edit-tags"
              className={styles.metaInput}
              type="text"
              value={Array.isArray(editForm.tags) ? editForm.tags.join(', ') : ''}
              onChange={(e) =>
                handleEditFieldChange(
                  'tags',
                  e.target.value.split(',').map((t) => t.trim()).filter(Boolean)
                )
              }
              placeholder="tag1, tag2"
            />
          </div>
        </div>
      ) : (
        (acc.accomplishment_date || acc.tags.length > 0) && (
          <div className={styles.meta}>
            {acc.accomplishment_date && <span>{acc.accomplishment_date}</span>}
            {acc.tags.length > 0 && (
              <div className={styles.tagList}>
                {acc.tags.map((tag) => (
                  <span key={tag} className={styles.tagBadge}>{tag}</span>
                ))}
              </div>
            )}
          </div>
        )
      )}

      <div className={styles.starSections}>
        {STAR_FIELDS.map(({ key, label, placeholder }) => (
          <SectionCard key={key} label={label}>
            {editing ? (
              <textarea
                className={styles.sectionTextarea}
                value={(editForm[key] as string) ?? ''}
                onChange={(e) => handleEditFieldChange(key, e.target.value)}
                placeholder={placeholder}
                rows={4}
              />
            ) : (
              acc[key] ? (
                <MarkdownContent>{acc[key] as string}</MarkdownContent>
              ) : (
                <p className={styles.placeholderText}>{placeholder}</p>
              )
            )}
          </SectionCard>
        ))}
      </div>

      {confirmDelete && (
        <ConfirmDialog
          message="Delete this accomplishment? This cannot be undone."
          onConfirm={handleDelete}
          onCancel={() => setConfirmDelete(false)}
        />
      )}
    </div>
  )
}
