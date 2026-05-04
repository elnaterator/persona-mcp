import { useCallback, useEffect, useState } from 'react'
import { Pencil, Trash2, Check, X, ChevronDown } from 'lucide-react'
import type { Communication } from '../types/resume'
import {
  listCommunications,
  addCommunication,
  updateCommunication,
  removeCommunication,
  listContactCommunications,
  addContactCommunication,
  updateContactCommunication,
  removeContactCommunication,
  listAllTags,
  ApiClientError,
} from '../services/api'
import { TagInput } from './TagInput'
import { ConfirmDialog } from './ConfirmDialog'
import { StatusMessage } from './StatusMessage'
import { AutoResizeTextarea } from './AutoResizeTextarea'
import { MarkdownContent } from './MarkdownContent'
import styles from './CommunicationsPanel.module.css'

const COMM_TYPES = ['email', 'phone', 'interview_note', 'other']
const COMM_DIRECTIONS = ['sent', 'received']
const COMM_STATUSES = ['draft', 'ready', 'sent', 'archived']

const STATUS_CLASS: Record<string, string> = {
  draft: styles.statusDraft,
  ready: styles.statusReady,
  sent: styles.statusSent,
  archived: styles.statusArchived,
}

export interface CommunicationsPanelProps {
  parentType: 'application' | 'contact'
  parentId: number
}

interface CommForm {
  type: string
  direction: string
  subject: string
  body: string
  date: string
  status: string
  tags: string[]
}

const today = () => new Date().toISOString().slice(0, 10)

const emptyForm: CommForm = {
  type: 'email',
  direction: 'sent',
  subject: '',
  body: '',
  date: today(),
  status: 'draft',
  tags: [],
}

export default function CommunicationsPanel({ parentType, parentId }: CommunicationsPanelProps) {
  const [communications, setCommunications] = useState<Communication[]>([])
  const [allTags, setAllTags] = useState<string[]>([])
  const [showAddForm, setShowAddForm] = useState(false)
  const [editTarget, setEditTarget] = useState<Communication | null>(null)
  const [deleteTarget, setDeleteTarget] = useState<number | null>(null)
  const [expandedIds, setExpandedIds] = useState<Set<number>>(new Set())
  const [form, setForm] = useState<CommForm>(emptyForm)
  const [submitting, setSubmitting] = useState(false)
  const [statusMessage, setStatusMessage] = useState<{ type: 'success' | 'error'; message: string } | null>(null)

  const toggleExpand = (id: number) =>
    setExpandedIds((prev) => {
      const next = new Set(prev)
      next.has(id) ? next.delete(id) : next.add(id)
      return next
    })

  const load = useCallback(async () => {
    try {
      const [data, tags] = await Promise.all([
        parentType === 'application'
          ? listCommunications(parentId)
          : listContactCommunications(parentId),
        listAllTags(),
      ])
      const sorted = [...data].sort(
        (a, b) => new Date(b.date).getTime() - new Date(a.date).getTime()
      )
      setCommunications(sorted)
      setAllTags(tags)
    } catch (err) {
      const msg = err instanceof ApiClientError ? err.detail ?? err.message : 'Failed to load communications'
      setStatusMessage({ type: 'error', message: msg })
    }
  }, [parentType, parentId])

  useEffect(() => {
    load()
  }, [load])

  const handleAdd = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      setSubmitting(true)
      const payload = {
        type: form.type,
        direction: form.direction,
        subject: form.subject.trim(),
        body: form.body.trim(),
        date: form.date,
        status: form.status,
        tags: form.tags,
      }
      if (parentType === 'application') {
        await addCommunication(parentId, payload)
      } else {
        await addContactCommunication(parentId, payload)
      }
      setForm(emptyForm)
      setShowAddForm(false)
      setStatusMessage({ type: 'success', message: 'Communication added' })
      await load()
    } catch (err) {
      const msg = err instanceof ApiClientError ? err.detail ?? err.message : 'Failed to add communication'
      setStatusMessage({ type: 'error', message: msg })
    } finally {
      setSubmitting(false)
    }
  }

  const startEdit = (comm: Communication) => {
    setEditTarget(comm)
    setForm({
      type: comm.type,
      direction: comm.direction,
      subject: comm.subject,
      body: comm.body,
      date: comm.date.slice(0, 10),
      status: comm.status,
      tags: comm.tags ?? [],
    })
    setShowAddForm(false)
  }

  const handleEditSave = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!editTarget) return
    try {
      setSubmitting(true)
      const payload = {
        type: form.type,
        direction: form.direction,
        subject: form.subject.trim(),
        body: form.body.trim(),
        date: form.date,
        status: form.status,
        tags: form.tags,
      }
      if (parentType === 'application') {
        await updateCommunication(parentId, editTarget.id, payload)
      } else {
        await updateContactCommunication(parentId, editTarget.id, payload)
      }
      setEditTarget(null)
      setForm(emptyForm)
      setStatusMessage({ type: 'success', message: 'Communication updated' })
      await load()
    } catch (err) {
      const msg = err instanceof ApiClientError ? err.detail ?? err.message : 'Failed to update communication'
      setStatusMessage({ type: 'error', message: msg })
    } finally {
      setSubmitting(false)
    }
  }

  const handleDelete = async () => {
    if (deleteTarget === null) return
    try {
      if (parentType === 'application') {
        await removeCommunication(parentId, deleteTarget)
      } else {
        await removeContactCommunication(parentId, deleteTarget)
      }
      setDeleteTarget(null)
      setStatusMessage({ type: 'success', message: 'Communication removed' })
      await load()
    } catch (err) {
      const msg = err instanceof ApiClientError ? err.detail ?? err.message : 'Failed to remove communication'
      setStatusMessage({ type: 'error', message: msg })
      setDeleteTarget(null)
    }
  }

  const formatDate = (iso: string) =>
    new Date(iso).toLocaleDateString(undefined, {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    })

  return (
    <div className={styles.container} id="communications" style={{ scrollMarginTop: 'var(--header-h, 64px)' }}>
      <div className={styles.panelHeader}>
        <h3 className={styles.panelTitle}>Communications</h3>
        {!showAddForm && (
          <button
            className={styles.addBtn}
            onClick={() => { setShowAddForm(true); setEditTarget(null) }}
          >
            Add Communication
          </button>
        )}
      </div>

      {statusMessage && (
        <StatusMessage
          type={statusMessage.type}
          message={statusMessage.message}
          onDismiss={() => setStatusMessage(null)}
        />
      )}

      {showAddForm && (
        <form className={styles.form} onSubmit={handleAdd}>
          <div className={styles.formHeader}>
            <button type="submit" className={styles.saveIconBtn} disabled={submitting} aria-label="Save">
              <Check size={14} />
            </button>
            <button
              type="button"
              className={styles.cancelIconBtn}
              onClick={() => { setShowAddForm(false); setForm(emptyForm) }}
              aria-label="Cancel"
            >
              <X size={14} />
            </button>
          </div>
          <CommFormFields form={form} onChange={(f) => setForm(f)} allTags={allTags} />
        </form>
      )}

      {communications.length === 0 && !showAddForm ? (
        <p className={styles.empty}>No communications yet.</p>
      ) : (
        <ul className={styles.timeline}>
          {communications.map((comm) => (
            <li key={comm.id} className={styles.timelineItem}>
              {editTarget?.id === comm.id ? (
                <form className={styles.form} onSubmit={handleEditSave}>
                  <div className={styles.formHeader}>
                    <button type="submit" className={styles.saveIconBtn} disabled={submitting} aria-label="Save">
                      <Check size={14} />
                    </button>
                    <button
                      type="button"
                      className={styles.cancelIconBtn}
                      onClick={() => { setEditTarget(null); setForm(emptyForm) }}
                      aria-label="Cancel"
                    >
                      <X size={14} />
                    </button>
                  </div>
                  <CommFormFields form={form} onChange={(f) => setForm(f)} allTags={allTags} />
                </form>
              ) : (
                <div
                  className={styles.commCard}
                  onClick={() => comm.body && toggleExpand(comm.id)}
                  style={{ cursor: comm.body ? 'pointer' : 'default' }}
                >
                  <div className={styles.commTopRow}>
                    <div className={styles.commMeta}>
                      <span className={styles.commDate}>{formatDate(comm.date)}</span>
                      <span className={styles.commType}>{comm.type}</span>
                      <span className={styles.commDirection}>{comm.direction}</span>
                      <span className={`${styles.statusBadge} ${STATUS_CLASS[comm.status] || ''}`}>
                        {comm.status}
                      </span>
                    </div>
                    <div className={styles.commRight}>
                      {comm.tags && comm.tags.length > 0 && (
                        <div className={styles.tagRow}>
                          {comm.tags.map((tag) => (
                            <span key={tag} className={styles.tagChip}>{tag}</span>
                          ))}
                        </div>
                      )}
                      <div className={styles.commActions}>
                        <button
                          className={styles.editBtn}
                          onClick={(e) => { e.stopPropagation(); startEdit(comm) }}
                          aria-label="Edit communication"
                        ><Pencil size={13} /></button>
                        <button
                          className={styles.deleteBtn}
                          onClick={(e) => { e.stopPropagation(); setDeleteTarget(comm.id) }}
                          aria-label="Delete communication"
                        ><Trash2 size={13} /></button>
                      </div>
                      {comm.body && (
                        <ChevronDown
                          size={14}
                          className={expandedIds.has(comm.id) ? styles.chevronOpen : styles.chevron}
                        />
                      )}
                    </div>
                  </div>
                  {(comm.subject || comm.body) && !expandedIds.has(comm.id) && (
                    <p className={styles.commSummaryRow}>
                      {comm.subject && <strong className={styles.commSubject}>{comm.subject}</strong>}
                      {comm.subject && comm.body && <span className={styles.commSep}> · </span>}
                      {comm.body && <span className={styles.commBodyPreview}>{comm.body}</span>}
                    </p>
                  )}
                  {expandedIds.has(comm.id) && (
                    <>
                      {comm.subject && <p className={styles.commSubjectExpanded}>{comm.subject}</p>}
                      {comm.body && (
                        <div className={styles.commBodyFull}>
                          <MarkdownContent>{comm.body}</MarkdownContent>
                        </div>
                      )}
                    </>
                  )}
                </div>
              )}
            </li>
          ))}
        </ul>
      )}

      {deleteTarget !== null && (
        <ConfirmDialog
          message="Remove this communication?"
          onConfirm={handleDelete}
          onCancel={() => setDeleteTarget(null)}
        />
      )}
    </div>
  )
}

interface CommFormFieldsProps {
  form: CommForm
  onChange: (form: CommForm) => void
  allTags: string[]
}

function CommFormFields({ form, onChange, allTags }: CommFormFieldsProps) {
  const set = (field: keyof Omit<CommForm, 'tags'>) =>
    (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) =>
      onChange({ ...form, [field]: e.target.value })

  return (
    <div className={styles.formGrid}>
      <div className={styles.formField}>
        <label className={styles.label} htmlFor="comm-type">Type</label>
        <select id="comm-type" className={styles.select} value={form.type} onChange={set('type')}>
          {COMM_TYPES.map((t) => <option key={t} value={t}>{t}</option>)}
        </select>
      </div>
      <div className={styles.formField}>
        <label className={styles.label} htmlFor="comm-direction">Direction</label>
        <select id="comm-direction" className={styles.select} value={form.direction} onChange={set('direction')}>
          {COMM_DIRECTIONS.map((d) => <option key={d} value={d}>{d}</option>)}
        </select>
      </div>
      <div className={styles.formField}>
        <label className={styles.label} htmlFor="comm-date">Date</label>
        <input id="comm-date" type="date" className={styles.input} value={form.date} onChange={set('date')} />
      </div>
      <div className={styles.formField}>
        <label className={styles.label} htmlFor="comm-status">Status</label>
        <select id="comm-status" className={styles.select} value={form.status} onChange={set('status')}>
          {COMM_STATUSES.map((s) => <option key={s} value={s}>{s}</option>)}
        </select>
      </div>
      <div className={`${styles.formField} ${styles.fullWidth}`}>
        <label className={styles.label} htmlFor="comm-subject">Subject</label>
        <input id="comm-subject" className={styles.input} value={form.subject} onChange={set('subject')} placeholder="Subject line" />
      </div>
      <div className={`${styles.formField} ${styles.fullWidth}`}>
        <label className={styles.label} htmlFor="comm-body">Body</label>
        <AutoResizeTextarea
          id="comm-body"
          className={styles.textarea}
          value={form.body}
          onChange={(val) => onChange({ ...form, body: val })}
          placeholder="Message body..."
        />
      </div>
      <div className={`${styles.formField} ${styles.fullWidth}`}>
        <label className={styles.label}>Tags</label>
        <TagInput
          value={form.tags}
          onChange={(tags) => onChange({ ...form, tags })}
          availableTags={allTags}
        />
      </div>
    </div>
  )
}
