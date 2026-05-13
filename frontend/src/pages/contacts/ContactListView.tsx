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
import styles from './ContactListView.module.css'

const RELATIONSHIP_SUGGESTIONS = [
  'Colleague',
  'Recruiter',
  'Manager',
  'Mentor',
  'Peer',
  'Friend',
  'Other',
]

interface FormState {
  name: string
  company: string
  title: string
  relationship: string
  tags: string[]
}

const EMPTY_FORM: FormState = {
  name: '',
  company: '',
  title: '',
  relationship: '',
  tags: [],
}

export default function ContactListView() {
  const navigate = useNavigate()
  const [tagFilter, setTagFilter] = useState<string[]>([])
  const [searchQuery, setSearchQuery] = useState('')
  const [showForm, setShowForm] = useState(false)
  const [form, setForm] = useState<FormState>(EMPTY_FORM)
  const [formError, setFormError] = useState('')

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
  const saving = create.isPending

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

  const handleFieldChange = (field: Exclude<keyof FormState, 'tags'>, value: string) => {
    setForm((prev) => ({ ...prev, [field]: value }))
  }

  const handleSave = async () => {
    if (!form.name.trim()) {
      setFormError('Name is required')
      return
    }
    setFormError('')
    try {
      await create.mutateAsync({
        name: form.name.trim(),
        company: form.company || undefined,
        title: form.title || undefined,
        relationship: form.relationship || undefined,
        tags: form.tags,
      })
      setForm(EMPTY_FORM)
      setShowForm(false)
      success('Contact created')
    } catch (err) {
      error(err instanceof Error ? err.message : 'Failed to create contact')
      setFormError(err instanceof Error ? err.message : 'Failed to create contact')
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
          onClick={() => {
            setShowForm((v) => !v)
            setFormError('')
          }}
        >
          {showForm ? 'Cancel' : 'New Contact'}
        </button>
      </div>

      {showForm && (
        <div className={styles.newForm}>
          <p className={styles.formTitle}>New Contact</p>
          {formError && <p className={styles.formError}>{formError}</p>}

          <div className={styles.formRow}>
            <div className={styles.formField}>
              <label className={styles.formLabel} htmlFor="contact-name">Name *</label>
              <input
                id="contact-name"
                className={styles.input}
                type="text"
                value={form.name}
                onChange={(e) => handleFieldChange('name', e.target.value)}
                placeholder="Full name"
              />
            </div>
            <div className={styles.formField}>
              <label className={styles.formLabel} htmlFor="contact-relationship">Relationship</label>
              <input
                id="contact-relationship"
                className={styles.input}
                type="text"
                list="relationship-suggestions"
                value={form.relationship}
                onChange={(e) => handleFieldChange('relationship', e.target.value)}
                placeholder="e.g. Recruiter"
              />
              <datalist id="relationship-suggestions">
                {RELATIONSHIP_SUGGESTIONS.map((r) => (
                  <option key={r} value={r} />
                ))}
              </datalist>
            </div>
          </div>

          <div className={styles.formRow}>
            <div className={styles.formField}>
              <label className={styles.formLabel} htmlFor="contact-company">Company</label>
              <input
                id="contact-company"
                className={styles.input}
                type="text"
                value={form.company}
                onChange={(e) => handleFieldChange('company', e.target.value)}
                placeholder="Company or organization"
              />
            </div>
            <div className={styles.formField}>
              <label className={styles.formLabel} htmlFor="contact-title">Title</label>
              <input
                id="contact-title"
                className={styles.input}
                type="text"
                value={form.title}
                onChange={(e) => handleFieldChange('title', e.target.value)}
                placeholder="Job title"
              />
            </div>
          </div>

          <div className={styles.formField}>
            <label className={styles.formLabel} htmlFor="contact-tags">Tags</label>
            <TagInput
              id="contact-tags"
              value={form.tags}
              onChange={(tags) => setForm((prev) => ({ ...prev, tags }))}
              availableTags={allTags}
              allowCreate={true}
              placeholder="Add tag..."
            />
          </div>

          <div className={styles.formActions}>
            <button
              className={styles.submitButton}
              onClick={handleSave}
              disabled={saving}
            >
              {saving ? 'Saving...' : 'Save'}
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
                <div className={styles.itemHeader}>
                  <span className={styles.itemName}>{contact.name}</span>
                  {contact.relationship && (
                    <span className={styles.relationshipBadge}>{contact.relationship}</span>
                  )}
                </div>
                {(contact.company || contact.title) && (
                  <div className={styles.itemSub}>
                    {[contact.title, contact.company].filter(Boolean).join(' · ')}
                  </div>
                )}
                <div className={styles.itemMeta}>
                  {contact.followup_date && (
                    <span className={styles.followupDate}>
                      Follow up: {contact.followup_date}
                    </span>
                  )}
                  <span>{new Date(contact.updated_at).toLocaleDateString()}</span>
                  {!!contact.link_count && (
                    <span className={styles.linkCount}><Link2 size={11} />{contact.link_count}</span>
                  )}
                </div>
                {contact.tags.length > 0 && (
                  <div className={styles.itemTags}>
                    {contact.tags.map((tag) => (
                      <span key={tag} className={styles.tagBadge}>{tag}</span>
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
