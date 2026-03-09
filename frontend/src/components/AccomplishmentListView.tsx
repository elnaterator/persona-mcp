import { useState, useEffect, useCallback } from 'react'
import { Link } from 'react-router'
import type { AccomplishmentSummary } from '../types/resume'
import {
  listAccomplishments,
  listAccomplishmentTags,
  createAccomplishment,
} from '../services/api'
import styles from './AccomplishmentListView.module.css'

interface FormState {
  title: string
  situation: string
  task: string
  action: string
  result: string
  accomplishment_date: string
  tags: string
}

const EMPTY_FORM: FormState = {
  title: '',
  situation: '',
  task: '',
  action: '',
  result: '',
  accomplishment_date: '',
  tags: '',
}

export default function AccomplishmentListView() {
  const [accomplishments, setAccomplishments] = useState<AccomplishmentSummary[]>([])
  const [allTags, setAllTags] = useState<string[]>([])
  const [tagFilter, setTagFilter] = useState('')
  const [showForm, setShowForm] = useState(false)
  const [form, setForm] = useState<FormState>(EMPTY_FORM)
  const [formError, setFormError] = useState('')
  const [saving, setSaving] = useState(false)

  const loadData = useCallback(async () => {
    const [accs, tags] = await Promise.all([
      listAccomplishments(tagFilter || undefined),
      listAccomplishmentTags(),
    ])
    setAccomplishments(accs)
    setAllTags(tags)
  }, [tagFilter])

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
      await createAccomplishment({
        title: form.title.trim(),
        situation: form.situation,
        task: form.task,
        action: form.action,
        result: form.result,
        accomplishment_date: form.accomplishment_date || null,
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
        <h2 className={styles.heading}>Accomplishments</h2>
        <button
          className={styles.newButton}
          onClick={() => {
            setShowForm((v) => !v)
            setFormError('')
          }}
        >
          {showForm ? 'Cancel' : 'New Accomplishment'}
        </button>
      </div>

      {showForm && (
        <div className={styles.newForm}>
          <p className={styles.formTitle}>New Accomplishment</p>
          {formError && <p className={styles.formError}>{formError}</p>}

          <div className={styles.formField}>
            <label className={styles.formLabel} htmlFor="acc-title">Title *</label>
            <input
              id="acc-title"
              className={styles.input}
              type="text"
              value={form.title}
              onChange={(e) => handleFieldChange('title', e.target.value)}
              placeholder="Brief title of the accomplishment"
            />
          </div>

          <div className={styles.formField}>
            <label className={styles.formLabel} htmlFor="acc-situation">Situation</label>
            <textarea
              id="acc-situation"
              className={styles.textarea}
              value={form.situation}
              onChange={(e) => handleFieldChange('situation', e.target.value)}
              placeholder="Describe the context or background…"
              rows={3}
            />
          </div>

          <div className={styles.formField}>
            <label className={styles.formLabel} htmlFor="acc-task">Task</label>
            <textarea
              id="acc-task"
              className={styles.textarea}
              value={form.task}
              onChange={(e) => handleFieldChange('task', e.target.value)}
              placeholder="What was your specific responsibility or goal?"
              rows={3}
            />
          </div>

          <div className={styles.formField}>
            <label className={styles.formLabel} htmlFor="acc-action">Action</label>
            <textarea
              id="acc-action"
              className={styles.textarea}
              value={form.action}
              onChange={(e) => handleFieldChange('action', e.target.value)}
              placeholder="What steps did you take to address the situation?"
              rows={3}
            />
          </div>

          <div className={styles.formField}>
            <label className={styles.formLabel} htmlFor="acc-result">Result</label>
            <textarea
              id="acc-result"
              className={styles.textarea}
              value={form.result}
              onChange={(e) => handleFieldChange('result', e.target.value)}
              placeholder="What was the outcome or impact? Include metrics where possible."
              rows={3}
            />
          </div>

          <div className={styles.formField}>
            <label className={styles.formLabel} htmlFor="acc-date">Accomplishment Date</label>
            <input
              id="acc-date"
              className={styles.input}
              type="date"
              value={form.accomplishment_date}
              onChange={(e) => handleFieldChange('accomplishment_date', e.target.value)}
            />
          </div>

          <div className={styles.formField}>
            <label className={styles.formLabel} htmlFor="acc-tags">Tags</label>
            <input
              id="acc-tags"
              className={styles.input}
              type="text"
              value={form.tags}
              onChange={(e) => handleFieldChange('tags', e.target.value)}
              placeholder="e.g. leadership, technical (comma-separated)"
              list="acc-tags-suggestions"
            />
            <datalist id="acc-tags-suggestions">
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
              {saving ? 'Saving…' : 'Save'}
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
          id="acc-tag-filter"
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
      </div>

      {accomplishments.length === 0 ? (
        <p className={styles.empty}>No accomplishments yet. Click "New Accomplishment" to add one.</p>
      ) : (
        <ul className={styles.list}>
          {accomplishments.map((acc) => (
            <li key={acc.id} className={styles.item}>
              <Link to={`/accomplishments/${acc.id}`} className={styles.itemLink}>
                <div className={styles.itemTitle}>{acc.title}</div>
                {acc.accomplishment_date && (
                  <div className={styles.itemMeta}>{acc.accomplishment_date}</div>
                )}
                {acc.tags.length > 0 && (
                  <div className={styles.itemTags}>
                    {acc.tags.map((tag) => (
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
