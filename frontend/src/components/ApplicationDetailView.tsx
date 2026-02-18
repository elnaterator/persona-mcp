import { useCallback, useEffect, useState } from 'react'
import type { Application, ResumeVersionSummary } from '../types/resume'
import {
  getApplication,
  updateApplication,
  deleteApplication,
  listResumes,
} from '../services/api'
import ContactsPanel from './ContactsPanel'
import CommunicationsPanel from './CommunicationsPanel'
import { ConfirmDialog } from './ConfirmDialog'
import { StatusMessage } from './StatusMessage'
import { LoadingSpinner } from './LoadingSpinner'
import styles from './ApplicationDetailView.module.css'

const ALL_STATUSES = [
  'Interested',
  'Applied',
  'Phone Screen',
  'Interview',
  'Offer',
  'Rejected',
  'Withdrawn',
  'Accepted',
]

interface ApplicationDetailViewProps {
  appId: number
  onBack: () => void
}

export default function ApplicationDetailView({ appId, onBack }: ApplicationDetailViewProps) {
  const [app, setApp] = useState<Application | null>(null)
  const [resumeVersions, setResumeVersions] = useState<ResumeVersionSummary[]>([])
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false)
  const [statusMessage, setStatusMessage] = useState<{ type: 'success' | 'error'; message: string } | null>(null)

  // Editable form state mirrors the app fields
  const [form, setForm] = useState<Partial<Application>>({})

  const load = useCallback(async () => {
    try {
      setLoading(true)
      const [appData, versions] = await Promise.all([
        getApplication(appId),
        listResumes(),
      ])
      setApp(appData)
      setForm(appData)
      setResumeVersions(versions)
    } catch {
      setStatusMessage({ type: 'error', message: 'Failed to load application' })
    } finally {
      setLoading(false)
    }
  }, [appId])

  useEffect(() => {
    load()
  }, [load])

  const handleSave = async () => {
    if (!form.company?.trim() || !form.position?.trim()) return
    try {
      setSaving(true)
      const updated = await updateApplication(appId, {
        company: form.company?.trim(),
        position: form.position?.trim(),
        status: form.status,
        url: form.url?.trim() || null,
        description: form.description?.trim() || '',
        notes: form.notes?.trim() || '',
        resume_version_id: form.resume_version_id ?? null,
      })
      setApp(updated)
      setForm(updated)
      setStatusMessage({ type: 'success', message: 'Application saved' })
    } catch {
      setStatusMessage({ type: 'error', message: 'Failed to save application' })
    } finally {
      setSaving(false)
    }
  }

  const handleDelete = async () => {
    try {
      await deleteApplication(appId)
      onBack()
    } catch {
      setStatusMessage({ type: 'error', message: 'Failed to delete application' })
      setShowDeleteConfirm(false)
    }
  }

  const setField = (field: keyof Application) =>
    (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
      const value = e.target.value
      setForm((prev) => ({ ...prev, [field]: value }))
    }

  if (loading) return <LoadingSpinner />
  if (!app) return null

  const isDirty = JSON.stringify(form) !== JSON.stringify(app)

  return (
    <div className={styles.container} data-testid="application-detail-view">
      <div className={styles.topBar}>
        <button className={styles.backButton} onClick={onBack}>
          Back to list
        </button>
        <button
          className={styles.deleteButton}
          onClick={() => setShowDeleteConfirm(true)}
        >
          Delete Application
        </button>
      </div>

      {statusMessage && (
        <StatusMessage
          type={statusMessage.type}
          message={statusMessage.message}
          onDismiss={() => setStatusMessage(null)}
        />
      )}

      <div className={styles.card}>
        <h2 className={styles.heading}>Application Details</h2>

        <div className={styles.formGrid}>
          <div className={styles.formField}>
            <label className={styles.label} htmlFor="app-company">Company *</label>
            <input
              id="app-company"
              className={styles.input}
              value={form.company || ''}
              onChange={setField('company')}
              placeholder="Company name"
            />
          </div>
          <div className={styles.formField}>
            <label className={styles.label} htmlFor="app-position">Position *</label>
            <input
              id="app-position"
              className={styles.input}
              value={form.position || ''}
              onChange={setField('position')}
              placeholder="Job title"
            />
          </div>
          <div className={styles.formField}>
            <label className={styles.label} htmlFor="app-status">Status</label>
            <select
              id="app-status"
              className={styles.select}
              value={form.status || 'Interested'}
              onChange={setField('status')}
            >
              {ALL_STATUSES.map((s) => (
                <option key={s} value={s}>{s}</option>
              ))}
            </select>
          </div>
          <div className={styles.formField}>
            <label className={styles.label} htmlFor="app-resume">Resume Version</label>
            <select
              id="app-resume"
              className={styles.select}
              value={form.resume_version_id ?? ''}
              onChange={(e) => setForm((prev) => ({
                ...prev,
                resume_version_id: e.target.value ? Number(e.target.value) : null,
              }))}
            >
              <option value="">-- None --</option>
              {resumeVersions.map((rv) => (
                <option key={rv.id} value={rv.id}>
                  {rv.label}{rv.is_default ? ' (default)' : ''}
                </option>
              ))}
            </select>
          </div>
          <div className={`${styles.formField} ${styles.fullWidth}`}>
            <label className={styles.label} htmlFor="app-url">URL</label>
            <input
              id="app-url"
              type="url"
              className={styles.input}
              value={form.url || ''}
              onChange={setField('url')}
              placeholder="https://..."
            />
          </div>
          <div className={`${styles.formField} ${styles.fullWidth}`}>
            <label className={styles.label} htmlFor="app-description">Description</label>
            <textarea
              id="app-description"
              className={styles.textarea}
              value={form.description || ''}
              onChange={setField('description')}
              rows={4}
              placeholder="Job description, requirements..."
            />
          </div>
          <div className={`${styles.formField} ${styles.fullWidth}`}>
            <label className={styles.label} htmlFor="app-notes">Notes</label>
            <textarea
              id="app-notes"
              className={styles.textarea}
              value={form.notes || ''}
              onChange={setField('notes')}
              rows={3}
              placeholder="Personal notes..."
            />
          </div>
        </div>

        <div className={styles.saveRow}>
          <button
            className={styles.saveButton}
            onClick={handleSave}
            disabled={saving || !isDirty || !form.company?.trim() || !form.position?.trim()}
          >
            {saving ? 'Saving...' : 'Save Changes'}
          </button>
          {isDirty && (
            <button
              className={styles.revertButton}
              onClick={() => setForm(app)}
            >
              Revert
            </button>
          )}
        </div>
      </div>

      <div className={styles.panels}>
        <ContactsPanel appId={appId} />
        <CommunicationsPanel appId={appId} />
      </div>

      {showDeleteConfirm && (
        <ConfirmDialog
          message={`Delete the application for "${app.position}" at "${app.company}"? This cannot be undone.`}
          onConfirm={handleDelete}
          onCancel={() => setShowDeleteConfirm(false)}
        />
      )}
    </div>
  )
}
