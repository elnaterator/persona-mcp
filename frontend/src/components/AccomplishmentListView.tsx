import { useState, useEffect, useCallback } from 'react'
import type { AccomplishmentSummary } from '../types/resume'
import {
  listAccomplishments,
  listAccomplishmentTags,
  createAccomplishment,
} from '../services/api'

interface Props {
  onSelectAccomplishment: (id: number) => void
}

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

export default function AccomplishmentListView({ onSelectAccomplishment }: Props) {
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
    <div className="section-container">
      <div className="section-header">
        <h2>Accomplishments</h2>
        <button
          className="btn btn-primary"
          onClick={() => {
            setShowForm((v) => !v)
            setFormError('')
          }}
        >
          {showForm ? 'Cancel' : 'New Accomplishment'}
        </button>
      </div>

      {showForm && (
        <div className="form-card">
          <h3>New Accomplishment</h3>
          {formError && <p className="form-error">{formError}</p>}

          <div className="form-group">
            <label htmlFor="acc-title">Title *</label>
            <input
              id="acc-title"
              type="text"
              value={form.title}
              onChange={(e) => handleFieldChange('title', e.target.value)}
              placeholder="Brief title of the accomplishment"
            />
          </div>

          <div className="form-group">
            <label htmlFor="acc-situation">Situation</label>
            <textarea
              id="acc-situation"
              value={form.situation}
              onChange={(e) => handleFieldChange('situation', e.target.value)}
              placeholder="Describe the context or background…"
              rows={3}
            />
          </div>

          <div className="form-group">
            <label htmlFor="acc-task">Task</label>
            <textarea
              id="acc-task"
              value={form.task}
              onChange={(e) => handleFieldChange('task', e.target.value)}
              placeholder="What was your specific responsibility or goal?"
              rows={3}
            />
          </div>

          <div className="form-group">
            <label htmlFor="acc-action">Action</label>
            <textarea
              id="acc-action"
              value={form.action}
              onChange={(e) => handleFieldChange('action', e.target.value)}
              placeholder="What steps did you take to address the situation?"
              rows={3}
            />
          </div>

          <div className="form-group">
            <label htmlFor="acc-result">Result</label>
            <textarea
              id="acc-result"
              value={form.result}
              onChange={(e) => handleFieldChange('result', e.target.value)}
              placeholder="What was the outcome or impact? Include metrics where possible."
              rows={3}
            />
          </div>

          <div className="form-group">
            <label htmlFor="acc-date">Accomplishment Date</label>
            <input
              id="acc-date"
              type="date"
              value={form.accomplishment_date}
              onChange={(e) => handleFieldChange('accomplishment_date', e.target.value)}
            />
          </div>

          <div className="form-group">
            <label htmlFor="acc-tags">Tags</label>
            <input
              id="acc-tags"
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

          <div className="form-actions">
            <button
              className="btn btn-primary"
              onClick={handleSave}
              disabled={saving}
            >
              {saving ? 'Saving…' : 'Save'}
            </button>
            <button
              className="btn btn-secondary"
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

      <div className="filter-bar">
        <label htmlFor="acc-tag-filter">Filter by tag:</label>
        <select
          id="acc-tag-filter"
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
        <p className="empty-state">No accomplishments yet. Click "New Accomplishment" to add one.</p>
      ) : (
        <ul className="item-list">
          {accomplishments.map((acc) => (
            <li key={acc.id} className="item-card" onClick={() => onSelectAccomplishment(acc.id)}>
              <div className="item-title">{acc.title}</div>
              {acc.accomplishment_date && (
                <div className="item-date">{acc.accomplishment_date}</div>
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
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
