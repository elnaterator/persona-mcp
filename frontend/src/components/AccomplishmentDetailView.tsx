import { useState, useEffect } from 'react'
import type { Accomplishment } from '../types/resume'
import { getAccomplishment, updateAccomplishment, deleteAccomplishment } from '../services/api'
import styles from './AccomplishmentDetailView.module.css'

interface Props {
  accomplishmentId: number
  onBack: () => void
}

export default function AccomplishmentDetailView({ accomplishmentId, onBack }: Props) {
  const [acc, setAcc] = useState<Accomplishment | null>(null)
  const [editing, setEditing] = useState(false)
  const [editForm, setEditForm] = useState<Partial<Accomplishment>>({})
  const [editError, setEditError] = useState('')
  const [saving, setSaving] = useState(false)
  const [confirmDelete, setConfirmDelete] = useState(false)
  const [deleting, setDeleting] = useState(false)

  useEffect(() => {
    getAccomplishment(accomplishmentId).then(setAcc)
  }, [accomplishmentId])

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
      const updated = await updateAccomplishment(accomplishmentId, {
        ...editForm,
        accomplishment_date: editForm.accomplishment_date || null,
        tags: editForm.tags as string[],
      })
      setAcc(updated)
      setEditing(false)
    } catch (err) {
      setEditError(err instanceof Error ? err.message : 'Failed to save')
    } finally {
      setSaving(false)
    }
  }

  const handleDelete = async () => {
    setDeleting(true)
    try {
      await deleteAccomplishment(accomplishmentId)
      onBack()
    } catch {
      setDeleting(false)
      setConfirmDelete(false)
    }
  }

  const STAR_FIELDS: { key: keyof Accomplishment; label: string; placeholder: string }[] = [
    { key: 'situation', label: 'Situation', placeholder: 'Describe the context or background…' },
    { key: 'task', label: 'Task', placeholder: 'What was your specific responsibility or goal?' },
    { key: 'action', label: 'Action', placeholder: 'What steps did you take to address the situation?' },
    { key: 'result', label: 'Result', placeholder: 'What was the outcome or impact? Include metrics where possible.' },
  ]

  if (editing) {
    return (
      <div className={styles.container}>
        <div className={styles.topBar}>
          <h2 className={styles.cardHeading}>Edit Accomplishment</h2>
        </div>

        <div className={styles.card}>
          {editError && <p className={styles.formError}>{editError}</p>}

          <div className={styles.formField}>
            <label className={styles.formLabel} htmlFor="edit-title">Title *</label>
            <input
              id="edit-title"
              className={styles.input}
              type="text"
              value={editForm.title ?? ''}
              onChange={(e) => handleEditFieldChange('title', e.target.value)}
            />
          </div>

          {STAR_FIELDS.map(({ key, label, placeholder }) => (
            <div key={key} className={styles.formField}>
              <label className={styles.formLabel} htmlFor={`edit-${key}`}>{label}</label>
              <textarea
                id={`edit-${key}`}
                className={styles.textarea}
                value={(editForm[key] as string) ?? ''}
                onChange={(e) => handleEditFieldChange(key, e.target.value)}
                placeholder={placeholder}
                rows={4}
              />
            </div>
          ))}

          <div className={styles.formField}>
            <label className={styles.formLabel} htmlFor="edit-date">Accomplishment Date</label>
            <input
              id="edit-date"
              className={styles.input}
              type="date"
              value={(editForm.accomplishment_date as string) ?? ''}
              onChange={(e) => handleEditFieldChange('accomplishment_date', e.target.value)}
            />
          </div>

          <div className={styles.formField}>
            <label className={styles.formLabel} htmlFor="edit-tags">Tags</label>
            <input
              id="edit-tags"
              className={styles.input}
              type="text"
              value={Array.isArray(editForm.tags) ? editForm.tags.join(', ') : ''}
              onChange={(e) =>
                handleEditFieldChange(
                  'tags',
                  e.target.value
                    .split(',')
                    .map((t) => t.trim())
                    .filter(Boolean)
                )
              }
              placeholder="e.g. leadership, technical (comma-separated)"
            />
          </div>

          <div className={styles.formActions}>
            <button className={styles.saveButton} onClick={handleSave} disabled={saving}>
              {saving ? 'Saving…' : 'Save'}
            </button>
            <button className={styles.cancelButton} onClick={() => setEditing(false)}>
              Cancel
            </button>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className={styles.container}>
      <div className={styles.topBar}>
        <button className={styles.backButton} onClick={onBack}>
          Back
        </button>
        <h2 className={styles.topBarTitle}>{acc.title}</h2>
        <div className={styles.topBarActions}>
          <button className={styles.editButton} onClick={startEdit}>
            Edit
          </button>
          <button className={styles.deleteButton} onClick={() => setConfirmDelete(true)}>
            Delete
          </button>
        </div>
      </div>

      {(acc.accomplishment_date || acc.tags.length > 0) && (
        <div className={styles.meta}>
          {acc.accomplishment_date && <span>{acc.accomplishment_date}</span>}
          {acc.tags.length > 0 && (
            <div className={styles.tagList}>
              {acc.tags.map((tag) => (
                <span key={tag} className={styles.tagBadge}>
                  {tag}
                </span>
              ))}
            </div>
          )}
        </div>
      )}

      <div className={styles.starSections}>
        {STAR_FIELDS.map(({ key, label, placeholder }) => (
          <div key={key} className={styles.starSection}>
            <h3>{label}</h3>
            {acc[key] ? (
              <p>{acc[key] as string}</p>
            ) : (
              <p className={styles.placeholderText}>{placeholder}</p>
            )}
          </div>
        ))}
      </div>

      {confirmDelete && (
        <div className={styles.confirmDialog}>
          <p>Are you sure you want to delete this accomplishment?</p>
          <button
            className={styles.confirmButton}
            onClick={handleDelete}
            disabled={deleting}
          >
            {deleting ? 'Deleting…' : 'Confirm'}
          </button>
          <button
            className={styles.cancelConfirmButton}
            onClick={() => setConfirmDelete(false)}
          >
            Cancel
          </button>
        </div>
      )}
    </div>
  )
}
