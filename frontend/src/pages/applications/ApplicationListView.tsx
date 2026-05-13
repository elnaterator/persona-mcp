import { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router'
import { Link2 } from 'lucide-react'
import {
  useAllTags,
  useApplicationList,
  useApplicationMutations,
} from '../../hooks/queries'
import { TagInput } from '../../components/TagInput'
import { LoadingSpinner } from '../../components/LoadingSpinner'
import { useToast } from '../../components/toast'
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

interface NewAppForm {
  company: string
  position: string
  status: string
  url: string
  notes: string
  description: string
  tags: string[]
}

const emptyForm: NewAppForm = {
  company: '',
  position: '',
  status: 'Interested',
  url: '',
  notes: '',
  description: '',
  tags: [],
}

export default function ApplicationListView() {
  const navigate = useNavigate()
  const [tagFilter, setTagFilter] = useState<string[]>([])
  const [statusFilter, setStatusFilter] = useState('')
  const [searchQuery, setSearchQuery] = useState('')
  const [showNewForm, setShowNewForm] = useState(false)
  const [newForm, setNewForm] = useState<NewAppForm>(emptyForm)
  const { success, error } = useToast()

  const listQuery = useApplicationList({
    status: statusFilter || undefined,
    q: searchQuery || undefined,
    tags: tagFilter,
  })
  const tagsQuery = useAllTags()
  const { create } = useApplicationMutations()

  const applications = listQuery.data ?? []
  const allTags = tagsQuery.data ?? []
  const loading = listQuery.isPending

  useEffect(() => {
    if (listQuery.isError) {
      error('Failed to load applications')
    }
  }, [listQuery.isError, error])

  const handleCreateSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!newForm.company.trim() || !newForm.position.trim()) return

    try {
      const created = await create.mutateAsync({
        company: newForm.company.trim(),
        position: newForm.position.trim(),
        status: newForm.status,
        url: newForm.url.trim() || null,
        notes: newForm.notes.trim(),
        description: newForm.description.trim(),
        tags: newForm.tags,
      })
      setShowNewForm(false)
      setNewForm(emptyForm)
      success('Application created')
      navigate(`/applications/${created.id}`)
    } catch {
      error('Failed to create application')
    }
  }
  const submitting = create.isPending

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
        <TagInput
          value={tagFilter}
          onChange={setTagFilter}
          availableTags={allTags}
          allowCreate={false}
          placeholder="Filter by tag..."
        />
      </div>

      {loading ? (
        <LoadingSpinner />
      ) : applications.length === 0 ? (
        <p className={styles.empty}>No applications found.</p>
      ) : (
        <ul className={styles.list}>
          {applications.map((app) => (
            <li key={app.id} className={styles.item}>
              <Link to={`/applications/${app.id}`} className={styles.itemLink}>
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
                  {!!app.link_count && (
                    <span className={styles.linkCount}><Link2 size={11} />{app.link_count}</span>
                  )}
                  {app.tags && app.tags.length > 0 && (
                    <div className={styles.tagList}>
                      {app.tags.map((tag) => (
                        <span key={tag} className={styles.tagBadge}>{tag}</span>
                      ))}
                    </div>
                  )}
                </div>
              </Link>
              {app.url && (
                <a
                  href={app.url}
                  className={styles.metaLink}
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  Job posting
                </a>
              )}
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
