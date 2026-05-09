import { useState, useCallback, useEffect } from 'react'
import { useParams, useNavigate, useLocation, Link } from 'react-router'
import { Pencil, Trash2, Check, X, Mail, Phone, Building2, Briefcase, MapPin, Linkedin, Calendar } from 'lucide-react'
import type { Contact } from '../../types'
import { getContact, updateContact, deleteContact, listAllTags, mapGroupedLinks } from '../../services/api'
import { TagInput } from '../../components/TagInput'
import Breadcrumb from '../../components/Breadcrumb'
import NotFound from '../../components/NotFound'
import { ConfirmDialog } from '../../components/ConfirmDialog'
import { StatusMessage } from '../../components/StatusMessage'
import { SectionCard } from '../../components/SectionCard'
import { MarkdownContent } from '../../components/MarkdownContent'
import { AutoResizeTextarea } from '../../components/AutoResizeTextarea'
import CommunicationsPanel from '../../components/CommunicationsPanel'
import { LinksPanel } from '../../components/LinksPanel'
import { useResourceDetail } from '../../hooks/useResourceDetail'
import styles from './ContactDetailView.module.css'

const RELATIONSHIP_SUGGESTIONS = [
  'Colleague',
  'Recruiter',
  'Manager',
  'Mentor',
  'Peer',
  'Friend',
  'Other',
]

export default function ContactDetailView() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const location = useLocation()
  const expandCommId = (location.state as { expandCommId?: number } | null)?.expandCommId

  const numericId = id && /^\d+$/.test(id) ? Number(id) : null

  const [allTags, setAllTags] = useState<string[]>([])
  const [notFound, setNotFound] = useState(false)
  const [forbidden, setForbidden] = useState(false)
  const [editing, setEditing] = useState(false)
  const [editForm, setEditForm] = useState<Partial<Contact>>({})
  const [editError, setEditError] = useState('')
  const [saving, setSaving] = useState(false)
  const [confirmDelete, setConfirmDelete] = useState(false)
  const [, setDeleting] = useState(false)
  const [statusMessage, setStatusMessage] = useState<{ type: 'success' | 'error'; message: string } | null>(null)

  const contactFetcher = useCallback(async (strId: string) => {
    try {
      return await getContact(Number(strId))
    } catch (err) {
      const status = (err as { status?: number })?.status
      if (status === 404) setNotFound(true)
      else if (status === 403) setForbidden(true)
      throw err
    }
  }, [])

  const { item: contact, setItem: setContact, refresh: reloadContact } = useResourceDetail<Contact>(id, contactFetcher)

  useEffect(() => {
    if (numericId === null) {
      navigate('/contacts', { replace: true })
      return
    }
    listAllTags().then(setAllTags).catch(() => {})
  }, [numericId, navigate])

  if (numericId === null) return null
  if (notFound) return <NotFound entityName="Contact" backTo="/contacts" backLabel="Back to Contacts" />
  if (forbidden) return (
    <NotFound
      entityName="Contact"
      backTo="/contacts"
      backLabel="Back to Contacts"
      heading="This contact isn't yours"
      message="This contact belongs to another account and cannot be accessed."
    />
  )
  if (!contact) return <div>Loading...</div>

  const startEdit = () => {
    setEditForm({ ...contact })
    setEditError('')
    setEditing(true)
  }

  const handleEditFieldChange = (field: keyof Contact, value: string | string[] | null) => {
    setEditForm((prev) => ({ ...prev, [field]: value }))
  }

  const handleSave = async () => {
    if (!editForm.name?.trim()) {
      setEditError('Name is required')
      return
    }
    setSaving(true)
    setEditError('')
    try {
      const updated = await updateContact(numericId, {
        name: editForm.name?.trim(),
        email: editForm.email || null,
        phone: editForm.phone || null,
        company: editForm.company || null,
        title: editForm.title || null,
        relationship: editForm.relationship || null,
        linkedin_url: editForm.linkedin_url || null,
        location: editForm.location || null,
        last_contacted_date: editForm.last_contacted_date || null,
        followup_date: editForm.followup_date || null,
        notes: editForm.notes,
        tags: editForm.tags as string[],
      })
      setContact(updated)
      setEditing(false)
      setStatusMessage({ type: 'success', message: 'Saved' })
    } catch (err) {
      setEditError(err instanceof Error ? err.message : 'Failed to save')
    } finally {
      setSaving(false)
    }
  }

  const handleDelete = async () => {
    setDeleting(true)
    try {
      await deleteContact(numericId)
      navigate('/contacts')
    } catch {
      setDeleting(false)
      setConfirmDelete(false)
      setStatusMessage({ type: 'error', message: 'Failed to delete contact' })
    }
  }

  return (
    <div className={styles.container}>
      <Breadcrumb
        items={[
          { label: 'Contacts', to: '/contacts' },
          { label: contact.name },
        ]}
      />

      <div className={styles.topBar}>
        <Link to="/contacts" className={styles.backButton}>Back</Link>
        {editing ? (
          <input
            className={styles.titleInput}
            type="text"
            value={editForm.name ?? ''}
            onChange={(e) => handleEditFieldChange('name', e.target.value)}
            autoFocus
          />
        ) : (
          <h2 className={styles.topBarTitle}>{contact.name}</h2>
        )}
        <div className={styles.topBarActions}>
          {editing ? (
            <>
              <button
                className={styles.saveIconButton}
                onClick={handleSave}
                disabled={saving}
                aria-label="Save contact"
              >
                <Check size={14} />
              </button>
              <button
                className={styles.cancelIconButton}
                onClick={() => setEditing(false)}
                aria-label="Cancel editing"
              >
                <X size={14} />
              </button>
            </>
          ) : (
            <>
              <button className={styles.editButton} onClick={startEdit} aria-label="Edit contact">
                <Pencil size={14} />
              </button>
              <button className={styles.deleteButton} onClick={() => setConfirmDelete(true)} aria-label="Delete contact">
                <Trash2 size={14} />
              </button>
            </>
          )}
        </div>
      </div>

      {editError && <p className={styles.formError}>{editError}</p>}

      {statusMessage && (
        <StatusMessage
          type={statusMessage.type}
          message={statusMessage.message}
          onDismiss={() => setStatusMessage(null)}
        />
      )}

      {editing ? (
        <div className={styles.editGrid}>
          <div className={styles.editFields}>
            <div className={styles.fieldRow}>
              <div className={styles.fieldGroup}>
                <label className={styles.fieldLabel}>Relationship</label>
                <input
                  className={styles.fieldInput}
                  type="text"
                  list="edit-relationship-suggestions"
                  value={editForm.relationship ?? ''}
                  onChange={(e) => handleEditFieldChange('relationship', e.target.value)}
                  placeholder="e.g. Recruiter"
                />
                <datalist id="edit-relationship-suggestions">
                  {RELATIONSHIP_SUGGESTIONS.map((r) => (
                    <option key={r} value={r} />
                  ))}
                </datalist>
              </div>
              <div className={styles.fieldGroup}>
                <label className={styles.fieldLabel}>Company</label>
                <input
                  className={styles.fieldInput}
                  type="text"
                  value={editForm.company ?? ''}
                  onChange={(e) => handleEditFieldChange('company', e.target.value)}
                  placeholder="Company"
                />
              </div>
            </div>
            <div className={styles.fieldRow}>
              <div className={styles.fieldGroup}>
                <label className={styles.fieldLabel}>Title</label>
                <input
                  className={styles.fieldInput}
                  type="text"
                  value={editForm.title ?? ''}
                  onChange={(e) => handleEditFieldChange('title', e.target.value)}
                  placeholder="Job title"
                />
              </div>
              <div className={styles.fieldGroup}>
                <label className={styles.fieldLabel}>Email</label>
                <input
                  className={styles.fieldInput}
                  type="email"
                  value={editForm.email ?? ''}
                  onChange={(e) => handleEditFieldChange('email', e.target.value)}
                  placeholder="email@example.com"
                />
              </div>
            </div>
            <div className={styles.fieldRow}>
              <div className={styles.fieldGroup}>
                <label className={styles.fieldLabel}>Phone</label>
                <input
                  className={styles.fieldInput}
                  type="text"
                  value={editForm.phone ?? ''}
                  onChange={(e) => handleEditFieldChange('phone', e.target.value)}
                  placeholder="+1 555 000 0000"
                />
              </div>
              <div className={styles.fieldGroup}>
                <label className={styles.fieldLabel}>Location</label>
                <input
                  className={styles.fieldInput}
                  type="text"
                  value={editForm.location ?? ''}
                  onChange={(e) => handleEditFieldChange('location', e.target.value)}
                  placeholder="City, Country"
                />
              </div>
            </div>
            <div className={styles.fieldRow}>
              <div className={styles.fieldGroup}>
                <label className={styles.fieldLabel}>LinkedIn URL</label>
                <input
                  className={styles.fieldInput}
                  type="url"
                  value={editForm.linkedin_url ?? ''}
                  onChange={(e) => handleEditFieldChange('linkedin_url', e.target.value)}
                  placeholder="https://linkedin.com/in/..."
                />
              </div>
            </div>
            <div className={styles.fieldRow}>
              <div className={styles.fieldGroup}>
                <label className={styles.fieldLabel}>Last Contacted</label>
                <input
                  className={styles.fieldInput}
                  type="date"
                  value={editForm.last_contacted_date ?? ''}
                  onChange={(e) => handleEditFieldChange('last_contacted_date', e.target.value)}
                />
              </div>
              <div className={styles.fieldGroup}>
                <label className={styles.fieldLabel}>Follow Up Date</label>
                <input
                  className={styles.fieldInput}
                  type="date"
                  value={editForm.followup_date ?? ''}
                  onChange={(e) => handleEditFieldChange('followup_date', e.target.value)}
                />
              </div>
            </div>
            <div className={styles.fieldGroup}>
              <label className={styles.fieldLabel}>Tags</label>
              <TagInput
                value={(editForm.tags as string[]) ?? []}
                onChange={(tags) => handleEditFieldChange('tags', tags)}
                availableTags={allTags}
                allowCreate={true}
              />
            </div>
          </div>
          <div className={styles.editNotes}>
            <label className={styles.fieldLabel}>Notes</label>
            <AutoResizeTextarea
              className={styles.notesTextarea}
              value={editForm.notes ?? ''}
              onChange={(value) => handleEditFieldChange('notes', value)}
              placeholder="Notes, comm preferences, interests..."
            />
          </div>
        </div>
      ) : (
        <>
          <div className={styles.viewGrid}>
            <div className={styles.viewFields}>
              {contact.relationship && (
                <div className={styles.relationshipBadge}>{contact.relationship}</div>
              )}
              <div className={styles.fieldList}>
                {contact.email && (
                  <div className={styles.fieldItem}>
                    <Mail size={14} className={styles.fieldIcon} />
                    <a href={`mailto:${contact.email}`} className={styles.fieldLink}>{contact.email}</a>
                  </div>
                )}
                {contact.phone && (
                  <div className={styles.fieldItem}>
                    <Phone size={14} className={styles.fieldIcon} />
                    <span>{contact.phone}</span>
                  </div>
                )}
                {contact.company && (
                  <div className={styles.fieldItem}>
                    <Building2 size={14} className={styles.fieldIcon} />
                    <span>{contact.company}</span>
                  </div>
                )}
                {contact.title && (
                  <div className={styles.fieldItem}>
                    <Briefcase size={14} className={styles.fieldIcon} />
                    <span>{contact.title}</span>
                  </div>
                )}
                {contact.location && (
                  <div className={styles.fieldItem}>
                    <MapPin size={14} className={styles.fieldIcon} />
                    <span>{contact.location}</span>
                  </div>
                )}
                {contact.linkedin_url && (
                  <div className={styles.fieldItem}>
                    <Linkedin size={14} className={styles.fieldIcon} />
                    <a href={contact.linkedin_url} target="_blank" rel="noopener noreferrer" className={styles.fieldLink}>
                      {contact.linkedin_url.replace(/^https?:\/\/(www\.)?linkedin\.com\/in\//, '').replace(/\/$/, '')}
                    </a>
                  </div>
                )}
                {contact.last_contacted_date && (
                  <div className={styles.fieldItem}>
                    <Calendar size={14} className={styles.fieldIcon} />
                    <span>Last contacted: {contact.last_contacted_date}</span>
                  </div>
                )}
                {contact.followup_date && (
                  <div className={styles.fieldItem}>
                    <Calendar size={14} className={styles.fieldIcon} />
                    <span className={styles.followupText}>Follow up: {contact.followup_date}</span>
                  </div>
                )}
              </div>
              {contact.tags.length > 0 && (
                <div className={styles.tagList}>
                  {contact.tags.map((tag) => (
                    <span key={tag} className={styles.tagBadge}>{tag}</span>
                  ))}
                </div>
              )}
              {contact.updated_at && (
                <span className={styles.updatedDate}>Updated {new Date(contact.updated_at).toLocaleDateString()}</span>
              )}
            </div>
            <SectionCard>
              {contact.notes ? (
                <MarkdownContent>{contact.notes}</MarkdownContent>
              ) : (
                <p className={styles.placeholderText}>No notes yet.</p>
              )}
            </SectionCard>
          </div>
          <CommunicationsPanel contactId={contact.id} initialExpandId={expandCommId} />
        </>
      )}

      <LinksPanel
        resourceType="contact"
        resourceId={numericId}
        links={mapGroupedLinks(contact.links as Record<string, unknown[]>)}
        onChange={reloadContact}
      />

      {confirmDelete && (
        <ConfirmDialog
          message="Delete this contact? This cannot be undone."
          onConfirm={handleDelete}
          onCancel={() => setConfirmDelete(false)}
        />
      )}
    </div>
  )
}
