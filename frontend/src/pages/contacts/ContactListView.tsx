import { useState, useEffect, useRef } from 'react'
import { Link, useNavigate } from 'react-router'
import { Link2 } from 'lucide-react'
import type { CommunicationSearchResult } from '../../types'
import {
  useAllTags,
  useCommunicationSearch,
  useContactList,
  useContactMutations,
} from '../../hooks/queries'
import { TagInput } from '../../components/TagInput'
import { useToast } from '../../components/toast'
import { ContactPanel } from './ContactPanel'
import type { ContactCreateInput } from '../../schemas/contact'
import styles from './ContactListView.module.css'

export default function ContactListView() {
  const navigate = useNavigate()
  const [tagFilter, setTagFilter] = useState<string[]>([])
  const [searchQuery, setSearchQuery] = useState('')
  const [showForm, setShowForm] = useState(false)

  // Comm search state
  const [showCommSearch, setShowCommSearch] = useState(false)
  const [commQ, setCommQ] = useState('')
  const [commTags, setCommTags] = useState<string[]>([])
  const [debouncedCommQ, setDebouncedCommQ] = useState('')
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  const listQuery = useContactList({ tags: tagFilter, q: searchQuery })
  const tagsQuery = useAllTags()
  const { create } = useContactMutations()
  const { success, error } = useToast()

  const contacts = listQuery.data ?? []
  const allTags = tagsQuery.data ?? []

  useEffect(() => {
    if (!showCommSearch) return
    if (debounceRef.current) clearTimeout(debounceRef.current)
    debounceRef.current = setTimeout(() => setDebouncedCommQ(commQ), 300)
    return () => {
      if (debounceRef.current) clearTimeout(debounceRef.current)
    }
  }, [commQ, showCommSearch])

  const commSearch = useCommunicationSearch({
    q: debouncedCommQ || undefined,
    tags: commTags,
    enabled: showCommSearch,
  })
  const commResults: CommunicationSearchResult[] = commSearch.data ?? []
  const commSearching = commSearch.isFetching

  const handleCreate = async (data: ContactCreateInput) => {
    try {
      await create.mutateAsync({
        name: data.name,
        email: data.email ?? undefined,
        phone: data.phone ?? undefined,
        company: data.company ?? undefined,
        title: data.title ?? undefined,
        relationship: data.relationship ?? undefined,
        linkedin_url: data.linkedin_url ?? undefined,
        location: data.location ?? undefined,
        last_contacted_date: data.last_contacted_date ?? null,
        followup_date: data.followup_date ?? null,
        notes: data.notes,
        tags: data.tags ?? [],
      })
      setShowForm(false)
      success('Contact created')
    } catch (err) {
      error(err instanceof Error ? err.message : 'Failed to create contact')
      throw err
    }
  }

  const handleCommResultClick = (result: CommunicationSearchResult) => {
    navigate(`/contacts/${result.parentId}`, { state: { expandCommId: result.id } })
  }

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <h2 className={styles.heading}>Contacts</h2>
        <button
          className={styles.newButton}
          onClick={() => setShowForm((v) => !v)}
        >
          {showForm ? 'Cancel' : 'New Contact'}
        </button>
      </div>

      {showForm && (
        <ContactPanel
          mode="create"
          allTags={allTags}
          onSave={handleCreate}
          onCancel={() => setShowForm(false)}
        />
      )}

      {/* Communication Search Panel */}
      <div className={styles.commSearchCard}>
        <button
          className={styles.commSearchToggle}
          onClick={() => setShowCommSearch((v) => !v)}
        >
          {showCommSearch ? '▾' : '▸'} Search Communications
        </button>
        {showCommSearch && (
          <div className={styles.commSearchBody}>
            <div className={styles.commSearchRow}>
              <input
                className={styles.commSearchInput}
                type="text"
                value={commQ}
                onChange={(e) => setCommQ(e.target.value)}
                placeholder="Search subject, body, contact..."
              />
            </div>
            <TagInput
              value={commTags}
              onChange={setCommTags}
              availableTags={allTags}
              allowCreate={false}
              placeholder="Filter by tag..."
            />
            {commSearching && <p className={styles.commSearchHint}>Searching...</p>}
            {!commSearching && commResults.length === 0 && (commQ || commTags.length > 0) && (
              <p className={styles.commSearchHint}>No results found.</p>
            )}
            {!commSearching && !commQ && commTags.length === 0 && (
              <p className={styles.commSearchHint}>Enter a search term or tag to find communications.</p>
            )}
            {commResults.length > 0 && (
              <ul className={styles.commResultList}>
                {commResults.map((r) => (
                  <li key={r.id} className={styles.commResultItem} onClick={() => handleCommResultClick(r)}>
                    <div className={styles.commResultHeader}>
                      <span className={styles.commResultDate}>{r.date.slice(0, 10)}</span>
                      <span className={styles.commResultType}>{r.type}</span>
                      <span className={styles.commResultDir}>{r.direction}</span>
                    </div>
                    <div className={styles.commResultParent}>{r.parentName}</div>
                    {r.subject && <div className={styles.commResultSubject}>{r.subject}</div>}
                  </li>
                ))}
              </ul>
            )}
          </div>
        )}
      </div>

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
          placeholder="Search contacts..."
        />
      </div>

      {contacts.length === 0 ? (
        <p className={styles.empty}>No contacts yet. Click &quot;New Contact&quot; to add one.</p>
      ) : (
        <ul className={styles.list}>
          {contacts.map((contact) => (
            <li key={contact.id} className={styles.item}>
              <Link to={`/contacts/${contact.id}`} className={styles.itemLink}>
                <div className={styles.itemRow1}>
                  <div className={styles.itemLeft}>
                    <span className={styles.itemName}>{contact.name}</span>
                    {contact.relationship && (
                      <span className={styles.relationshipBadge}>{contact.relationship}</span>
                    )}
                  </div>
                  <div className={styles.itemRight}>
                    {contact.tags.length > 0 && (
                      <div className={styles.tagList}>
                        {contact.tags.map((tag) => (
                          <span key={tag} className={styles.tagBadge}>{tag}</span>
                        ))}
                      </div>
                    )}
                    <span className={styles.updatedDate}>Updated {new Date(contact.updated_at).toLocaleDateString()}</span>
                  </div>
                </div>
                {((contact.company || contact.title) || contact.followup_date || !!contact.link_count) && (
                  <div className={styles.itemRow2}>
                    {(contact.company || contact.title) && (
                      <span className={styles.itemSub}>
                        {[contact.title, contact.company].filter(Boolean).join(' · ')}
                      </span>
                    )}
                    {contact.followup_date && (
                      <span className={styles.followupDate}>
                        Follow up: {contact.followup_date}
                      </span>
                    )}
                    {!!contact.link_count && (
                      <span className={styles.linkCount}><Link2 size={11} />{contact.link_count}</span>
                    )}
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
