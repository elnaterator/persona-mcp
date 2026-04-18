import { useCallback, useEffect, useState } from 'react'
import { Pencil, Trash2, Check, X } from 'lucide-react'
import type { Communication } from '../types/resume'
import {
  listCommunications,
  addCommunication,
  updateCommunication,
  removeCommunication,
} from '../services/api'
import { ConfirmDialog } from './ConfirmDialog'
import { StatusMessage } from './StatusMessage'
import styles from './CommunicationsPanel.module.css'

const COMM_TYPES = ['Email', 'Phone', 'In-Person', 'Video', 'Message', 'Other']
const COMM_DIRECTIONS = ['Inbound', 'Outbound']
const COMM_STATUSES = ['draft', 'ready', 'sent', 'archived']

const STATUS_CLASS: Record<string, string> = {
  draft: styles.statusDraft,
  ready: styles.statusReady,
  sent: styles.statusSent,
  archived: styles.statusArchived,
}

interface CommunicationsPanelProps {
  appId: number
}

interface CommForm {
  type: string
  direction: string
  subject: string
  body: string
  date: string
  status: string
}

const today = () => new Date().toISOString().slice(0, 10)

const emptyForm: CommForm = {
  type: 'Email',
  direction: 'Outbound',
  subject: '',
  body: '',
  date: today(),
  status: 'draft',
}

export default function CommunicationsPanel({ appId }: CommunicationsPanelProps) {
  const [communications, setCommunications] = useState<Communication[]>([])
  const [showAddForm, setShowAddForm] = useState(false)
  const [editTarget, setEditTarget] = useState<Communication | null>(null)
  const [deleteTarget, setDeleteTarget] = useState<number | null>(null)
  const [form, setForm] = useState<CommForm>(emptyForm)
  const [submitting, setSubmitting] = useState(false)
  const [statusMessage, setStatusMessage] = useState<{ type: 'success' | 'error'; message: string } | null>(null)

  const load = useCallback(async () => {
    try {
      const data = await listCommunications(appId)
      // Sort by date descending
      const sorted = [...data].sort(
        (a, b) => new Date(b.date).getTime() - new Date(a.date).getTime()
      )
      setCommunications(sorted)
    } catch {
      setStatusMessage({ type: 'error', message: 'Failed to load communications' })
    }
  }, [appId])

  useEffect(() => {
    load()
  }, [load])

  const handleAdd = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      setSubmitting(true)
      await addCommunication(appId, {
        type: form.type,
        direction: form.direction,
        subject: form.subject.trim(),
        body: form.body.trim(),
        date: form.date,
        status: form.status,
      })
      setForm(emptyForm)
      setShowAddForm(false)
      setStatusMessage({ type: 'success', message: 'Communication added' })
      await load()
    } catch {
      setStatusMessage({ type: 'error', message: 'Failed to add communication' })
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
    })
    setShowAddForm(false)
  }

  const handleEditSave = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!editTarget) return
    try {
      setSubmitting(true)
      await updateCommunication(appId, editTarget.id, {
        type: form.type,
        direction: form.direction,
        subject: form.subject.trim(),
        body: form.body.trim(),
        date: form.date,
        status: form.status,
      })
      setEditTarget(null)
      setForm(emptyForm)
      setStatusMessage({ type: 'success', message: 'Communication updated' })
      await load()
    } catch {
      setStatusMessage({ type: 'error', message: 'Failed to update communication' })
    } finally {
      setSubmitting(false)
    }
  }

  const handleDelete = async () => {
    if (deleteTarget === null) return
    try {
      await removeCommunication(appId, deleteTarget)
      setDeleteTarget(null)
      setStatusMessage({ type: 'success', message: 'Communication removed' })
      await load()
    } catch {
      setStatusMessage({ type: 'error', message: 'Failed to remove communication' })
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
    <div className={styles.container}>
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
          <CommFormFields form={form} onChange={(f) => setForm(f)} />
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
                  <CommFormFields form={form} onChange={(f) => setForm(f)} />
                </form>
              ) : (
                <>
                  <div className={styles.commHeader}>
                    <div className={styles.commMeta}>
                      <span className={styles.commDate}>{formatDate(comm.date)}</span>
                      <span className={styles.commType}>{comm.type}</span>
                      <span className={styles.commDirection}>{comm.direction}</span>
                      <span className={`${styles.statusBadge} ${STATUS_CLASS[comm.status] || ''}`}>
                        {comm.status}
                      </span>
                    </div>
                    <div className={styles.commActions}>
                      <button className={styles.editBtn} onClick={() => startEdit(comm)} aria-label="Edit communication"><Pencil size={13} /></button>
                      <button className={styles.deleteBtn} onClick={() => setDeleteTarget(comm.id)} aria-label="Delete communication"><Trash2 size={13} /></button>
                    </div>
                  </div>
                  {comm.subject && <p className={styles.commSubject}>{comm.subject}</p>}
                  {comm.body && <p className={styles.commBody}>{comm.body}</p>}
                </>
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
}

function CommFormFields({ form, onChange }: CommFormFieldsProps) {
  const set = (field: keyof CommForm) =>
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
        <textarea id="comm-body" className={styles.textarea} value={form.body} onChange={set('body')} rows={4} placeholder="Message body..." />
      </div>
    </div>
  )
}
