import { useState, useEffect } from 'react'
import { useParams, useNavigate, Link } from 'react-router'
import type { Note } from '../types/resume'
import { getNote, updateNote, deleteNote } from '../services/api'
import Breadcrumb from './Breadcrumb'
import NotFound from './NotFound'
import styles from './NoteDetailView.module.css'

export default function NoteDetailView() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()

  const numericId = id && /^\d+$/.test(id) ? Number(id) : null

  const [note, setNote] = useState<Note | null>(null)
  const [notFound, setNotFound] = useState(false)
  const [forbidden, setForbidden] = useState(false)
  const [editing, setEditing] = useState(false)
  const [editForm, setEditForm] = useState<Partial<Note>>({})
  const [editError, setEditError] = useState('')
  const [saving, setSaving] = useState(false)
  const [confirmDelete, setConfirmDelete] = useState(false)
  const [deleting, setDeleting] = useState(false)

  useEffect(() => {
    if (numericId === null) {
      navigate('/notes', { replace: true })
      return
    }
    getNote(numericId).then(setNote).catch((err: unknown) => {
      const status = (err as { status?: number })?.status
      if (status === 404) {
        setNotFound(true)
      } else if (status === 403) {
        setForbidden(true)
      }
    })
  }, [numericId, navigate])

  if (numericId === null) return null
  if (notFound) return <NotFound entityName="Note" backTo="/notes" backLabel="Back to Notes" />
  if (forbidden) return <NotFound entityName="Note" backTo="/notes" backLabel="Back to Notes" heading="This note isn't yours" message="This note belongs to another account and cannot be accessed." />
  if (!note) {
    return <div>Loading...</div>
  }

  const startEdit = () => {
    setEditForm({
      title: note.title,
      content: note.content,
      tags: note.tags,
    })
    setEditError('')
    setEditing(true)
  }

  const handleEditFieldChange = (field: keyof Note, value: string | string[]) => {
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
      const updated = await updateNote(numericId, {
        title: editForm.title.trim(),
        content: editForm.content,
        tags: editForm.tags as string[],
      })
      setNote(updated)
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
      await deleteNote(numericId)
      navigate('/notes')
    } catch {
      setDeleting(false)
      setConfirmDelete(false)
    }
  }

  if (editing) {
    return (
      <div className={styles.container}>
        <div className={styles.topBar}>
          <h2 className={styles.cardHeading}>Edit Note</h2>
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

          <div className={styles.formField}>
            <label className={styles.formLabel} htmlFor="edit-content">Content</label>
            <textarea
              id="edit-content"
              className={styles.textarea}
              value={editForm.content ?? ''}
              onChange={(e) => handleEditFieldChange('content', e.target.value)}
              placeholder="Write your note here..."
              rows={8}
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
              placeholder="e.g. personal, career (comma-separated)"
            />
          </div>

          <div className={styles.formActions}>
            <button className={styles.saveButton} onClick={handleSave} disabled={saving}>
              {saving ? 'Saving...' : 'Save'}
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
      <Breadcrumb
        items={[
          { label: 'Notes', to: '/notes' },
          { label: note.title },
        ]}
      />

      <div className={styles.topBar}>
        <Link to="/notes" className={styles.backButton}>
          Back
        </Link>
        <h2 className={styles.topBarTitle}>{note.title}</h2>
        <div className={styles.topBarActions}>
          <button className={styles.editButton} onClick={startEdit}>
            Edit
          </button>
          <button className={styles.deleteButton} onClick={() => setConfirmDelete(true)}>
            Delete
          </button>
        </div>
      </div>

      {note.tags.length > 0 && (
        <div className={styles.meta}>
          <div className={styles.tagList}>
            {note.tags.map((tag) => (
              <span key={tag} className={styles.tagBadge}>
                {tag}
              </span>
            ))}
          </div>
        </div>
      )}

      <div className={styles.contentSection}>
        {note.content ? (
          <p>{note.content}</p>
        ) : (
          <p className={styles.placeholderText}>No content yet.</p>
        )}
      </div>

      {confirmDelete && (
        <div className={styles.confirmDialog}>
          <p>Are you sure you want to delete this note?</p>
          <button
            className={styles.confirmButton}
            onClick={handleDelete}
            disabled={deleting}
          >
            {deleting ? 'Deleting...' : 'Confirm'}
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
