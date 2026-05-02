import { useState, useEffect, useCallback } from 'react'
import { Link } from 'react-router'
import type { ContactSummary } from '../types/resume'
import { listContacts, createContact, listAllTags } from '../services/api'
import { TagInput } from './TagInput'
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
  const [contacts, setContacts] = useState<ContactSummary[]>([])
  const [allTags, setAllTags] = useState<string[]>([])
  const [tagFilter, setTagFilter] = useState<string[]>([])
  const [searchQuery, setSearchQuery] = useState('')
  const [showForm, setShowForm] = useState(false)
  const [form, setForm] = useState<FormState>(EMPTY_FORM)
  const [formError, setFormError] = useState('')
  const [saving, setSaving] = useState(false)

  const loadData = useCallback(async () => {
    const [contactList, tags] = await Promise.all([
      listContacts(tagFilter.length ? tagFilter : undefined, searchQuery || undefined),
      listAllTags(),
    ])
    setContacts(contactList)
    setAllTags(tags)
  }, [tagFilter, searchQuery])

  useEffect(() => {
    loadData()
  }, [loadData])

  const handleFieldChange = (field: Exclude<keyof FormState, 'tags'>, value: string) => {
    setForm((prev) => ({ ...prev, [field]: value }))
  }

  const handleSave = async () => {
    if (!form.name.trim()) {
      setFormError('Name is required')
      return
    }
    setSaving(true)
    setFormError('')
    try {
      await createContact({
        name: form.name.trim(),
        company: form.company || undefined,
        title: form.title || undefined,
        relationship: form.relationship || undefined,
        tags: form.tags,
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
