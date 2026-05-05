import { useState, useEffect, useCallback } from 'react'
import { Link } from 'react-router'
import { Link2 } from 'lucide-react'
import type { NoteSummary } from '../types/resume'
import {
  listNotes,
  createNote,
  listAllTags,
} from '../services/api'
import { TagInput } from './TagInput'
import styles from './NoteListView.module.css'

interface FormState {
  title: string
  content: string
  tags: string[]
}

const EMPTY_FORM: FormState = {
  title: '',
  content: '',
  tags: [],
}

export default function NoteListView() {
  const [notes, setNotes] = useState<NoteSummary[]>([])
  const [allTags, setAllTags] = useState<string[]>([])
  const [tagFilter, setTagFilter] = useState<string[]>([])
  const [searchQuery, setSearchQuery] = useState('')
  const [showForm, setShowForm] = useState(false)
  const [form, setForm] = useState<FormState>(EMPTY_FORM)
  const [formError, setFormError] = useState('')
  const [saving, setSaving] = useState(false)

  const loadData = useCallback(async () => {
    const [noteList, tags] = await Promise.all([
      listNotes(tagFilter.length ? tagFilter : undefined, searchQuery || undefined),
      listAllTags(),
    ])
    setNotes(noteList)
    setAllTags(tags)
  }, [tagFilter, searchQuery])

  useEffect(() => {
    loadData()
  }, [loadData])

  const handleFieldChange = (field: Exclude<keyof FormState, 'tags'>, value: string) => {
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
      await createNote({
        title: form.title.trim(),
        content: form.content,
        tags: form.tags,
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
            <TagInput
              id="note-tags"
              value={form.tags}
              onChange={(tags) => setForm((prev) => ({ ...prev, tags }))}
              availableTags={allTags}
              allowCreate={true}
              placeholder="Add tag..."
            />
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
        <TagInput
          value={tagFilter}
          onChange={setTagFilter}
          availableTags={allTags}
          allowCreate={false}
          placeholder="Filter by tag..."
        />
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
                  {!!note.link_count && (
                    <span className={styles.linkCount}><Link2 size={11} />{note.link_count}</span>
                  )}
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
