import { useState, useEffect, useCallback } from 'react'
import { Link } from 'react-router'
import type { NoteSummary } from '../types/resume'
import {
  listNotes,
  listNoteTags,
  listAccomplishmentTags,
  createNote,
} from '../services/api'
import styles from './NoteListView.module.css'

interface FormState {
  title: string
  content: string
  tags: string
}

const EMPTY_FORM: FormState = {
  title: '',
  content: '',
  tags: '',
}

export default function NoteListView() {
  const [notes, setNotes] = useState<NoteSummary[]>([])
  const [allTags, setAllTags] = useState<string[]>([])
  const [tagFilter, setTagFilter] = useState('')
  const [searchQuery, setSearchQuery] = useState('')
  const [showForm, setShowForm] = useState(false)
  const [form, setForm] = useState<FormState>(EMPTY_FORM)
  const [formError, setFormError] = useState('')
  const [saving, setSaving] = useState(false)

  const loadData = useCallback(async () => {
    const [noteList, noteTags, accTags] = await Promise.all([
      listNotes(tagFilter || undefined, searchQuery || undefined),
      listNoteTags(),
      listAccomplishmentTags(),
    ])
    setNotes(noteList)
    // Merge and deduplicate tags from notes and accomplishments
    const merged = Array.from(new Set([...noteTags, ...accTags])).sort()
    setAllTags(merged)
  }, [tagFilter, searchQuery])

  useEffect(() => {
    loadData()
  }, [loadData])

  const handleFieldChange = (field: keyof FormState, value: string) => {
    setForm((prev) => ({ ...prev, [field]: value }))
  }

  const handleSave = async () => {
    if (!form.title.trim()) {
      setFormError('Title is required')
      return
    }
    setSaving(true)
    setFormError('')
    try {
      const tags = form.tags
        .split(',')
        .map((t) => t.trim())
        .filter(Boolean)
      await createNote({
        title: form.title.trim(),
        content: form.content,
        tags,
      })
      setForm(EMPTY_FORM)
      setShowForm(false)
      await loadData()
    } catch (err) {
      setFormError(err instanceof Error ? err.message : 'Failed to save')
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <h2 className={styles.heading}>Notes</h2>
        <button
          className={styles.newButton}
          onClick={() => {
            setShowForm((v) => !v)
            setFormError('')
          }}
        >
          {showForm ? 'Cancel' : 'New Note'}
        </button>
      </div>

      {showForm && (
        <div className={styles.newForm}>
          <p className={styles.formTitle}>New Note</p>
          {formError && <p className={styles.formError}>{formError}</p>}

          <div className={styles.formField}>
            <label className={styles.formLabel} htmlFor="note-title">Title *</label>
            <input
              id="note-title"
              className={styles.input}
              type="text"
              value={form.title}
              onChange={(e) => handleFieldChange('title', e.target.value)}
              placeholder="Note title"
            />
          </div>

          <div className={styles.formField}>
            <label className={styles.formLabel} htmlFor="note-content">Content</label>
            <textarea
              id="note-content"
              className={styles.textarea}
              value={form.content}
              onChange={(e) => handleFieldChange('content', e.target.value)}
              placeholder="Write your note here..."
              rows={4}
            />
          </div>

          <div className={styles.formField}>
            <label className={styles.formLabel} htmlFor="note-tags">Tags</label>
            <input
              id="note-tags"
              className={styles.input}
              type="text"
              value={form.tags}
              onChange={(e) => handleFieldChange('tags', e.target.value)}
              placeholder="e.g. personal, career (comma-separated)"
              list="note-tags-suggestions"
            />
            <datalist id="note-tags-suggestions">
              {allTags.map((tag) => (
                <option key={tag} value={tag} />
              ))}
            </datalist>
          </div>

          <div className={styles.formActions}>
            <button
              className={styles.submitButton}
              onClick={handleSave}
              disabled={saving}
            >
              {saving ? 'Saving...' : 'Save'}
            </button>
            <button
              className={styles.cancelButton}
              onClick={() => {
                setShowForm(false)
                setFormError('')
                setForm(EMPTY_FORM)
              }}
            >
              Cancel
            </button>
          </div>
        </div>
      )}

      <div className={styles.filters}>
        <select
          id="note-tag-filter"
          className={styles.filterSelect}
          value={tagFilter}
          onChange={(e) => setTagFilter(e.target.value)}
        >
          <option value="">All tags</option>
          {allTags.map((tag) => (
            <option key={tag} value={tag}>
              {tag}
            </option>
          ))}
        </select>
        <input
          className={styles.searchInput}
          type="text"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          placeholder="Search notes..."
        />
      </div>

      {notes.length === 0 ? (
        <p className={styles.empty}>No notes yet. Click &quot;New Note&quot; to add one.</p>
      ) : (
        <ul className={styles.list}>
          {notes.map((note) => (
            <li key={note.id} className={styles.item}>
              <Link to={`/notes/${note.id}`} className={styles.itemLink}>
                <div className={styles.itemTitle}>{note.title}</div>
                <div className={styles.itemMeta}>
                  <span>{new Date(note.updated_at).toLocaleDateString()}</span>
                </div>
                {note.tags.length > 0 && (
                  <div className={styles.itemTags}>
                    {note.tags.map((tag) => (
                      <span key={tag} className={styles.tagBadge}>
                        {tag}
                      </span>
                    ))}
                  </div>
                )}
              </Link>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
