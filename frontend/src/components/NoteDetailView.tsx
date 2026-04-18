import { useState, useEffect, useRef } from 'react'
import { useParams, useNavigate, Link } from 'react-router'
import { Pencil, Trash2, Check, X } from 'lucide-react'
import type { Note } from '../types/resume'
import { getNote, updateNote, deleteNote } from '../services/api'
import Breadcrumb from './Breadcrumb'
import NotFound from './NotFound'
import { ConfirmDialog } from './ConfirmDialog'
import { StatusMessage } from './StatusMessage'
import { SectionCard } from './SectionCard'
import { MarkdownContent } from './MarkdownContent'
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
  const contentTextareaRef = useRef<HTMLTextAreaElement>(null)
  const [confirmDelete, setConfirmDelete] = useState(false)
  const [, setDeleting] = useState(false)
  const [statusMessage, setStatusMessage] = useState<{ type: 'success' | 'error'; message: string } | null>(null)

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

  useEffect(() => {
    const el = contentTextareaRef.current
    if (!el) return
    el.style.height = 'auto'
    el.style.height = `${el.scrollHeight}px`
  }, [editForm.content, editing])

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
      await deleteNote(numericId)
      navigate('/notes')
    } catch {
      setDeleting(false)
      setConfirmDelete(false)
      setStatusMessage({ type: 'error', message: 'Failed to delete note' })
    }
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
        <Link to="/notes" className={styles.backButton}>Back</Link>
        {editing ? (
          <input
            className={styles.titleInput}
            type="text"
            value={editForm.title ?? ''}
            onChange={(e) => handleEditFieldChange('title', e.target.value)}
            autoFocus
          />
        ) : (
          <h2 className={styles.topBarTitle}>{note.title}</h2>
        )}
        <div className={styles.topBarActions}>
          {editing ? (
            <>
              <button
                className={styles.saveIconButton}
                onClick={handleSave}
                disabled={saving}
                aria-label="Save note"
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
              <button className={styles.editButton} onClick={startEdit} aria-label="Edit note">
                <Pencil size={14} />
              </button>
              <button className={styles.deleteButton} onClick={() => setConfirmDelete(true)} aria-label="Delete note">
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
        <div className={styles.meta}>
          {note.tags.length > 0 && (
            <div className={styles.tagList}>
              {note.tags.map((tag) => (
                <span key={tag} className={styles.tagBadge}>{tag}</span>
              ))}
            </div>
          )}
          {note.updated_at && (
            <span className={styles.updatedDate}>Updated {new Date(note.updated_at).toLocaleDateString()}</span>
          )}
        </div>
      )}

      <SectionCard>
        {editing ? (
          <textarea
            ref={contentTextareaRef}
            className={styles.contentTextarea}
            value={editForm.content ?? ''}
            onChange={(e) => handleEditFieldChange('content', e.target.value)}
            placeholder="Write your note here..."
          />
        ) : (
          note.content ? (
            <MarkdownContent>{note.content}</MarkdownContent>
          ) : (
            <p className={styles.placeholderText}>No content yet.</p>
          )
        )}
      </SectionCard>

      {confirmDelete && (
        <ConfirmDialog
          message="Delete this note? This cannot be undone."
          onConfirm={handleDelete}
          onCancel={() => setConfirmDelete(false)}
        />
      )}
    </div>
  )
}
