import { useEffect, useState } from 'react'
import type { Application } from '../types/resume'
import { listApplications, createApplication } from '../services/api'
import { LoadingSpinner } from './LoadingSpinner'
import { StatusMessage } from './StatusMessage'
import styles from './ApplicationListView.module.css'

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

const STATUS_COLORS: Record<string, string> = {
  Interested: styles.statusInterested,
  Applied: styles.statusApplied,
  'Phone Screen': styles.statusPhoneScreen,
  Interview: styles.statusInterview,
  Offer: styles.statusOffer,
  Rejected: styles.statusRejected,
  Withdrawn: styles.statusWithdrawn,
  Accepted: styles.statusAccepted,
}

interface ApplicationListViewProps {
  onSelectApp: (id: number) => void
}

interface NewAppForm {
  company: string
  position: string
  status: string
  url: string
  notes: string
  description: string
}

const emptyForm: NewAppForm = {
  company: '',
  position: '',
  status: 'Interested',
  url: '',
  notes: '',
  description: '',
}

export default function ApplicationListView({ onSelectApp }: ApplicationListViewProps) {
  const [applications, setApplications] = useState<Application[]>([])
  const [loading, setLoading] = useState(true)
  const [statusFilter, setStatusFilter] = useState('')
  const [searchQuery, setSearchQuery] = useState('')
  const [showNewForm, setShowNewForm] = useState(false)
  const [newForm, setNewForm] = useState<NewAppForm>(emptyForm)
  const [submitting, setSubmitting] = useState(false)
  const [statusMessage, setStatusMessage] = useState<{ type: 'success' | 'error'; message: string } | null>(null)

  const load = async (status?: string, q?: string) => {
    try {
      setLoading(true)
      const data = await listApplications(status || undefined, q || undefined)
      setApplications(data)
    } catch {
      setStatusMessage({ type: 'error', message: 'Failed to load applications' })
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    load(statusFilter, searchQuery)
  }, [statusFilter, searchQuery])

  const handleCreateSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!newForm.company.trim() || !newForm.position.trim()) return

    try {
      setSubmitting(true)
      const created = await createApplication({
        company: newForm.company.trim(),
        position: newForm.position.trim(),
        status: newForm.status,
        url: newForm.url.trim() || null,
        notes: newForm.notes.trim(),
        description: newForm.description.trim(),
      })
      setShowNewForm(false)
      setNewForm(emptyForm)
      setStatusMessage({ type: 'success', message: 'Application created' })
      onSelectApp(created.id)
    } catch {
      setStatusMessage({ type: 'error', message: 'Failed to create application' })
    } finally {
      setSubmitting(false)
    }
  }

  const formatDate = (iso: string) =>
    new Date(iso).toLocaleDateString(undefined, {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    })

  return (
    <div className={styles.container} data-testid="application-list-view">
      <div className={styles.header}>
        <h2 className={styles.heading}>Job Applications</h2>
        <button
          className={styles.newButton}
          onClick={() => setShowNewForm((v) => !v)}
        >
          {showNewForm ? 'Cancel' : 'New Application'}
        </button>
      </div>

      {statusMessage && (
        <StatusMessage
          type={statusMessage.type}
          message={statusMessage.message}
          onDismiss={() => setStatusMessage(null)}
        />
      )}

      {showNewForm && (
        <form className={styles.newForm} onSubmit={handleCreateSubmit}>
          <h3 className={styles.formTitle}>New Application</h3>
          <div className={styles.formGrid}>
            <div className={styles.formField}>
              <label className={styles.formLabel} htmlFor="new-company">
                Company *
              </label>
              <input
                id="new-company"
                className={styles.input}
                value={newForm.company}
                onChange={(e) => setNewForm((f) => ({ ...f, company: e.target.value }))}
                placeholder="Company name"
                required
              />
            </div>
            <div className={styles.formField}>
              <label className={styles.formLabel} htmlFor="new-position">
                Position *
              </label>
              <input
                id="new-position"
                className={styles.input}
                value={newForm.position}
                onChange={(e) => setNewForm((f) => ({ ...f, position: e.target.value }))}
                placeholder="Job title"
                required
              />
            </div>
            <div className={styles.formField}>
              <label className={styles.formLabel} htmlFor="new-status">
                Status
              </label>
              <select
                id="new-status"
                className={styles.select}
                value={newForm.status}
                onChange={(e) => setNewForm((f) => ({ ...f, status: e.target.value }))}
              >
                {ALL_STATUSES.map((s) => (
                  <option key={s} value={s}>{s}</option>
                ))}
              </select>
            </div>
            <div className={styles.formField}>
              <label className={styles.formLabel} htmlFor="new-url">
                URL
              </label>
              <input
                id="new-url"
                className={styles.input}
                type="url"
                value={newForm.url}
                onChange={(e) => setNewForm((f) => ({ ...f, url: e.target.value }))}
                placeholder="https://..."
              />
            </div>
          </div>
          <div className={styles.formActions}>
            <button
              type="submit"
              className={styles.submitButton}
              disabled={submitting || !newForm.company.trim() || !newForm.position.trim()}
            >
              {submitting ? 'Creating...' : 'Create Application'}
            </button>
            <button
              type="button"
              className={styles.cancelButton}
              onClick={() => { setShowNewForm(false); setNewForm(emptyForm) }}
            >
              Cancel
            </button>
          </div>
        </form>
      )}

      <div className={styles.filters}>
        <select
          className={styles.filterSelect}
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          aria-label="Filter by status"
        >
          <option value="">All statuses</option>
          {ALL_STATUSES.map((s) => (
            <option key={s} value={s}>{s}</option>
          ))}
        </select>
        <input
          className={styles.searchInput}
          type="search"
          placeholder="Search company or position..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          aria-label="Search applications"
        />
      </div>

      {loading ? (
        <LoadingSpinner />
      ) : applications.length === 0 ? (
        <p className={styles.empty}>No applications found.</p>
      ) : (
        <ul className={styles.list}>
          {applications.map((app) => (
            <li
              key={app.id}
              className={styles.item}
              onClick={() => onSelectApp(app.id)}
              role="button"
              tabIndex={0}
              onKeyDown={(e) => e.key === 'Enter' && onSelectApp(app.id)}
            >
              <div className={styles.itemHeader}>
                <div className={styles.itemTitle}>
                  <span className={styles.position}>{app.position}</span>
                  <span className={styles.company}>{app.company}</span>
                </div>
                <span className={`${styles.statusBadge} ${STATUS_COLORS[app.status] || ''}`}>
                  {app.status}
                </span>
              </div>
              <div className={styles.itemMeta}>
                <span className={styles.metaDate}>Updated {formatDate(app.updated_at)}</span>
                {app.url && (
                  <a
                    href={app.url}
                    className={styles.metaLink}
                    target="_blank"
                    rel="noopener noreferrer"
                    onClick={(e) => e.stopPropagation()}
                  >
                    Job posting
                  </a>
                )}
              </div>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
