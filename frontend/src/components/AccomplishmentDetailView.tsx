import { useState, useEffect } from 'react'
import type { Accomplishment } from '../types/resume'
import { getAccomplishment, updateAccomplishment, deleteAccomplishment } from '../services/api'

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
      <div className="section-container">
        <div className="section-header">
          <h2>Edit Accomplishment</h2>
        </div>

        {editError && <p className="form-error">{editError}</p>}

        <div className="form-group">
          <label htmlFor="edit-title">Title *</label>
          <input
            id="edit-title"
            type="text"
            value={editForm.title ?? ''}
            onChange={(e) => handleEditFieldChange('title', e.target.value)}
          />
        </div>

        {STAR_FIELDS.map(({ key, label, placeholder }) => (
          <div key={key} className="form-group">
            <label htmlFor={`edit-${key}`}>{label}</label>
            <textarea
              id={`edit-${key}`}
              value={(editForm[key] as string) ?? ''}
              onChange={(e) => handleEditFieldChange(key, e.target.value)}
              placeholder={placeholder}
              rows={4}
            />
          </div>
        ))}

        <div className="form-group">
          <label htmlFor="edit-date">Accomplishment Date</label>
          <input
            id="edit-date"
            type="date"
            value={(editForm.accomplishment_date as string) ?? ''}
            onChange={(e) => handleEditFieldChange('accomplishment_date', e.target.value)}
          />
        </div>

        <div className="form-group">
          <label htmlFor="edit-tags">Tags</label>
          <input
            id="edit-tags"
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

        <div className="form-actions">
          <button className="btn btn-primary" onClick={handleSave} disabled={saving}>
            {saving ? 'Saving…' : 'Save'}
          </button>
          <button className="btn btn-secondary" onClick={() => setEditing(false)}>
            Cancel
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="section-container">
      <div className="section-header">
        <button className="btn btn-secondary" onClick={onBack}>
          Back
        </button>
        <h2>{acc.title}</h2>
        <div className="header-actions">
          <button className="btn btn-secondary" onClick={startEdit}>
            Edit
          </button>
          <button className="btn btn-danger" onClick={() => setConfirmDelete(true)}>
            Delete
          </button>
        </div>
      </div>

      {acc.accomplishment_date && (
        <p className="item-date">Date: {acc.accomplishment_date}</p>
      )}

      {acc.tags.length > 0 && (
        <div className="item-tags">
          {acc.tags.map((tag) => (
            <span key={tag} className="tag-badge">
              {tag}
            </span>
          ))}
        </div>
      )}

      <div className="star-sections">
        {STAR_FIELDS.map(({ key, label, placeholder }) => (
          <div key={key} className="star-section">
            <h3>{label}</h3>
            {acc[key] ? (
              <p>{acc[key] as string}</p>
            ) : (
              <p className="placeholder-text">{placeholder}</p>
            )}
          </div>
        ))}
      </div>

      {confirmDelete && (
        <div className="confirm-dialog">
          <p>Are you sure you want to delete this accomplishment?</p>
          <button
            className="btn btn-danger"
            onClick={handleDelete}
            disabled={deleting}
          >
            {deleting ? 'Deleting…' : 'Confirm'}
          </button>
          <button
            className="btn btn-secondary"
            onClick={() => setConfirmDelete(false)}
          >
            Cancel
          </button>
        </div>
      )}
    </div>
  )
}
