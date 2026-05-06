import { useState, useEffect, useMemo } from 'react'
import { X } from 'lucide-react'
import type { ResourceRef, ResourceType } from '../types'
import {
  listApplications,
  listAccomplishments,
  listResumes,
  listNotes,
  listContacts,
} from '../services/api'
import styles from './LinkPickerModal.module.css'

type TabId = 'all' | ResourceType

const TABS: { id: TabId; label: string }[] = [
  { id: 'all', label: 'All' },
  { id: 'application', label: 'Applications' },
  { id: 'accomplishment', label: 'Accomplishments' },
  { id: 'resume', label: 'Resumes' },
  { id: 'note', label: 'Notes' },
  { id: 'contact', label: 'Contacts' },
]

interface LinkPickerModalProps {
  excludeRefs: ResourceRef[]
  onPick: (ref: ResourceRef) => void
  onClose: () => void
}

function isExcluded(ref: ResourceRef, excludeRefs: ResourceRef[]): boolean {
  return excludeRefs.some((e) => e.type === ref.type && e.id === ref.id)
}

async function fetchAll(): Promise<ResourceRef[]> {
  const [apps, accs, resumes, notes, contacts] = await Promise.all([
    listApplications().catch(() => []),
    listAccomplishments().catch(() => []),
    listResumes().catch(() => []),
    listNotes().catch(() => []),
    listContacts().catch(() => []),
  ])

  const refs: ResourceRef[] = [
    ...apps.map((a) => ({
      type: 'application' as const,
      id: a.id,
      name: a.position ? `${a.company} – ${a.position}` : a.company,
      updatedAt: a.updated_at,
    })),
    ...accs.map((a) => ({
      type: 'accomplishment' as const,
      id: a.id,
      name: a.title,
      updatedAt: a.updated_at,
    })),
    ...resumes.map((r) => ({
      type: 'resume' as const,
      id: r.id,
      name: r.label,
      updatedAt: r.updated_at,
    })),
    ...notes.map((n) => ({
      type: 'note' as const,
      id: n.id,
      name: n.title,
      updatedAt: n.updated_at,
    })),
    ...contacts.map((c) => ({
      type: 'contact' as const,
      id: c.id,
      name: c.name,
      updatedAt: c.updated_at,
    })),
  ]

  refs.sort((a, b) => {
    if (a.updatedAt && b.updatedAt) {
      return b.updatedAt.localeCompare(a.updatedAt)
    }
    return 0
  })

  return refs
}

async function fetchForType(type: ResourceType): Promise<ResourceRef[]> {
  switch (type) {
    case 'application': {
      const items = await listApplications()
      return items.map((a) => ({
        type: 'application' as const,
        id: a.id,
        name: a.position ? `${a.company} – ${a.position}` : a.company,
        updatedAt: a.updated_at,
      }))
    }
    case 'accomplishment': {
      const items = await listAccomplishments()
      return items.map((a) => ({
        type: 'accomplishment' as const,
        id: a.id,
        name: a.title,
        updatedAt: a.updated_at,
      }))
    }
    case 'resume': {
      const items = await listResumes()
      return items.map((r) => ({
        type: 'resume' as const,
        id: r.id,
        name: r.label,
        updatedAt: r.updated_at,
      }))
    }
    case 'note': {
      const items = await listNotes()
      return items.map((n) => ({
        type: 'note' as const,
        id: n.id,
        name: n.title,
        updatedAt: n.updated_at,
      }))
    }
    case 'contact': {
      const items = await listContacts()
      return items.map((c) => ({
        type: 'contact' as const,
        id: c.id,
        name: c.name,
        updatedAt: c.updated_at,
      }))
    }
  }
}

export function LinkPickerModal({
  excludeRefs,
  onPick,
  onClose,
}: LinkPickerModalProps) {
  const [activeTab, setActiveTab] = useState<TabId>('all')
  const [query, setQuery] = useState('')
  const [allRefs, setAllRefs] = useState<ResourceRef[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    setLoading(true)
    const fn = activeTab === 'all' ? fetchAll() : fetchForType(activeTab)
    fn.then((refs) => {
      setAllRefs(refs)
      setLoading(false)
    }).catch(() => {
      setAllRefs([])
      setLoading(false)
    })
  }, [activeTab])

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase()
    return allRefs.filter((ref) => {
      if (isExcluded(ref, excludeRefs)) return false
      if (q && !ref.name.toLowerCase().includes(q)) return false
      return true
    })
  }, [allRefs, excludeRefs, query])

  return (
    <div className={styles.overlay} onClick={(e) => e.target === e.currentTarget && onClose()}>
      <div className={styles.modal} role="dialog" aria-modal="true" aria-label="Link picker">
        <div className={styles.modalHeader}>
          <h3 className={styles.modalTitle}>Link to resource</h3>
          <button className={styles.closeButton} onClick={onClose} aria-label="Close">
            <X size={16} />
          </button>
        </div>

        <div className={styles.toolbar}>
          <div className={styles.tabsScroll}>
            {TABS.map((tab) => (
              <button
                key={tab.id}
                className={`${styles.tab} ${activeTab === tab.id ? styles.tabActive : ''}`}
                onClick={() => setActiveTab(tab.id)}
              >
                {tab.label}
              </button>
            ))}
          </div>
          <input
            className={styles.filterInput}
            type="text"
            placeholder="filter..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            autoFocus
          />
        </div>

        <div className={styles.resultsList}>
          {loading ? (
            <div className={styles.loading}>Loading...</div>
          ) : filtered.length === 0 ? (
            <div className={styles.empty}>No results</div>
          ) : (
            filtered.map((ref) => (
              <button
                key={`${ref.type}/${ref.id}`}
                className={styles.resultRow}
                onClick={() => onPick(ref)}
              >
                {activeTab === 'all' && (
                  <span className={styles.typeBadge}>{ref.type}</span>
                )}
                <span className={styles.resultName}>{ref.name}</span>
              </button>
            ))
          )}
        </div>
      </div>
    </div>
  )
}
