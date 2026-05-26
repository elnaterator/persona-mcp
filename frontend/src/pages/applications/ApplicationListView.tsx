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
import { APPLICATION_STATUSES } from '../../schemas/application'
import { ApplicationPanel } from './ApplicationPanel'
import type { ApplicationPanelInput } from './ApplicationPanel'
import styles from './ApplicationListView.module.css'

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

export default function ApplicationListView() {
  const navigate = useNavigate()
  const [tagFilter, setTagFilter] = useState<string[]>([])
  const [statusFilter, setStatusFilter] = useState('')
  const [searchQuery, setSearchQuery] = useState('')
  const [showNewForm, setShowNewForm] = useState(false)
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

  const onCreate = async (data: ApplicationPanelInput) => {
    try {
      const created = await create.mutateAsync({
        company: data.company,
        position: data.position,
        status: data.status,
        url: data.url ?? undefined,
        description: data.description ?? undefined,
        notes: data.notes ?? undefined,
        tags: data.tags ?? [],
      })
      setShowNewForm(false)
      success('Application created')
      navigate(`/applications/${created.id}`)
    } catch {
      error('Failed to create application')
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

      {showNewForm && (
        <ApplicationPanel
          mode="create"
          allTags={allTags}
          onSave={onCreate}
          onCancel={() => setShowNewForm(false)}
        />
      )}

      <div className={styles.filters}>
        <select
          className={styles.filterSelect}
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          aria-label="Filter by status"
        >
          <option value="">All statuses</option>
          {APPLICATION_STATUSES.map((s) => (
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
                <div className={styles.itemMain}>
                  <span className={styles.position}>{app.position}</span>
                  <span className={styles.company}>{app.company}</span>
                  <span className={`${styles.statusBadge} ${STATUS_COLORS[app.status] || ''}`}>
                    {app.status}
                  </span>
                </div>
                {app.tags && app.tags.length > 0 && (
                  <div className={styles.tagList}>
                    {app.tags.map((tag) => (
                      <span key={tag} className={styles.tagBadge}>{tag}</span>
                    ))}
                  </div>
                )}
                <div className={styles.itemMeta}>
                  <span>Updated {formatDate(app.updated_at)}</span>
                  {!!app.link_count && (
                    <span className={styles.linkCount}><Link2 size={11} />{app.link_count}</span>
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
