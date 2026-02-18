import { useCallback, useEffect, useState } from 'react'
import type { ApplicationContact } from '../types/resume'
import { listContacts, addContact, updateAppContact, removeContact } from '../services/api'
import { ConfirmDialog } from './ConfirmDialog'
import { StatusMessage } from './StatusMessage'
import styles from './ContactsPanel.module.css'

interface ContactsPanelProps {
  appId: number
}

interface ContactForm {
  name: string
  role: string
  email: string
  phone: string
  notes: string
}

const emptyForm: ContactForm = {
  name: '',
  role: '',
  email: '',
  phone: '',
  notes: '',
}

export default function ContactsPanel({ appId }: ContactsPanelProps) {
  const [contacts, setContacts] = useState<ApplicationContact[]>([])
  const [showAddForm, setShowAddForm] = useState(false)
  const [editTarget, setEditTarget] = useState<ApplicationContact | null>(null)
  const [deleteTarget, setDeleteTarget] = useState<number | null>(null)
  const [form, setForm] = useState<ContactForm>(emptyForm)
  const [submitting, setSubmitting] = useState(false)
  const [statusMessage, setStatusMessage] = useState<{ type: 'success' | 'error'; message: string } | null>(null)

  const load = useCallback(async () => {
    try {
      const data = await listContacts(appId)
      setContacts(data)
    } catch {
      setStatusMessage({ type: 'error', message: 'Failed to load contacts' })
    }
  }, [appId])

  useEffect(() => {
    load()
  }, [load])

  const handleAdd = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!form.name.trim()) return
    try {
      setSubmitting(true)
      await addContact(appId, {
        name: form.name.trim(),
        role: form.role.trim() || null,
        email: form.email.trim() || null,
        phone: form.phone.trim() || null,
        notes: form.notes.trim(),
      })
      setForm(emptyForm)
      setShowAddForm(false)
      setStatusMessage({ type: 'success', message: 'Contact added' })
      await load()
    } catch {
      setStatusMessage({ type: 'error', message: 'Failed to add contact' })
    } finally {
      setSubmitting(false)
    }
  }

  const startEdit = (contact: ApplicationContact) => {
    setEditTarget(contact)
    setForm({
      name: contact.name,
      role: contact.role || '',
      email: contact.email || '',
      phone: contact.phone || '',
      notes: contact.notes || '',
    })
    setShowAddForm(false)
  }

  const handleEditSave = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!editTarget || !form.name.trim()) return
    try {
      setSubmitting(true)
      await updateAppContact(appId, editTarget.id, {
        name: form.name.trim(),
        role: form.role.trim() || null,
        email: form.email.trim() || null,
        phone: form.phone.trim() || null,
        notes: form.notes.trim(),
      })
      setEditTarget(null)
      setForm(emptyForm)
      setStatusMessage({ type: 'success', message: 'Contact updated' })
      await load()
    } catch {
      setStatusMessage({ type: 'error', message: 'Failed to update contact' })
    } finally {
      setSubmitting(false)
    }
  }

  const handleDelete = async () => {
    if (deleteTarget === null) return
    try {
      await removeContact(appId, deleteTarget)
      setDeleteTarget(null)
      setStatusMessage({ type: 'success', message: 'Contact removed' })
      await load()
    } catch {
      setStatusMessage({ type: 'error', message: 'Failed to remove contact' })
      setDeleteTarget(null)
    }
  }

  const cancelEdit = () => {
    setEditTarget(null)
    setForm(emptyForm)
  }

  return (
    <div className={styles.container}>
      <div className={styles.panelHeader}>
        <h3 className={styles.panelTitle}>Contacts</h3>
        <button
          className={styles.addBtn}
          onClick={() => { setShowAddForm((v) => !v); setEditTarget(null) }}
        >
          {showAddForm ? 'Cancel' : 'Add Contact'}
        </button>
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
          <ContactFormFields form={form} onChange={(f) => setForm(f)} />
          <div className={styles.formActions}>
            <button type="submit" className={styles.saveBtn} disabled={submitting || !form.name.trim()}>
              {submitting ? 'Saving...' : 'Add'}
            </button>
            <button type="button" className={styles.cancelBtn} onClick={() => { setShowAddForm(false); setForm(emptyForm) }}>
              Cancel
            </button>
          </div>
        </form>
      )}

      {contacts.length === 0 && !showAddForm ? (
        <p className={styles.empty}>No contacts yet.</p>
      ) : (
        <ul className={styles.list}>
          {contacts.map((contact) => (
            <li key={contact.id} className={styles.contactItem}>
              {editTarget?.id === contact.id ? (
                <form className={styles.form} onSubmit={handleEditSave}>
                  <ContactFormFields form={form} onChange={(f) => setForm(f)} />
                  <div className={styles.formActions}>
                    <button type="submit" className={styles.saveBtn} disabled={submitting || !form.name.trim()}>
                      {submitting ? 'Saving...' : 'Save'}
                    </button>
                    <button type="button" className={styles.cancelBtn} onClick={cancelEdit}>
                      Cancel
                    </button>
                  </div>
                </form>
              ) : (
                <>
                  <div className={styles.contactInfo}>
                    <span className={styles.contactName}>{contact.name}</span>
                    {contact.role && <span className={styles.contactRole}>{contact.role}</span>}
                    {contact.email && <span className={styles.contactDetail}>{contact.email}</span>}
                    {contact.phone && <span className={styles.contactDetail}>{contact.phone}</span>}
                    {contact.notes && <p className={styles.contactNotes}>{contact.notes}</p>}
                  </div>
                  <div className={styles.contactActions}>
                    <button className={styles.editBtn} onClick={() => startEdit(contact)}>Edit</button>
                    <button className={styles.deleteBtn} onClick={() => setDeleteTarget(contact.id)}>Delete</button>
                  </div>
                </>
              )}
            </li>
          ))}
        </ul>
      )}

      {deleteTarget !== null && (
        <ConfirmDialog
          message="Remove this contact?"
          onConfirm={handleDelete}
          onCancel={() => setDeleteTarget(null)}
        />
      )}
    </div>
  )
}

interface ContactFormFieldsProps {
  form: ContactForm
  onChange: (form: ContactForm) => void
}

function ContactFormFields({ form, onChange }: ContactFormFieldsProps) {
  const set = (field: keyof ContactForm) => (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) =>
    onChange({ ...form, [field]: e.target.value })

  return (
    <div className={styles.formGrid}>
      <div className={styles.formField}>
        <label className={styles.label} htmlFor="contact-name">Name *</label>
        <input id="contact-name" className={styles.input} value={form.name} onChange={set('name')} required />
      </div>
      <div className={styles.formField}>
        <label className={styles.label} htmlFor="contact-role">Role</label>
        <input id="contact-role" className={styles.input} value={form.role} onChange={set('role')} />
      </div>
      <div className={styles.formField}>
        <label className={styles.label} htmlFor="contact-email">Email</label>
        <input id="contact-email" type="email" className={styles.input} value={form.email} onChange={set('email')} />
      </div>
      <div className={styles.formField}>
        <label className={styles.label} htmlFor="contact-phone">Phone</label>
        <input id="contact-phone" type="tel" className={styles.input} value={form.phone} onChange={set('phone')} />
      </div>
      <div className={`${styles.formField} ${styles.fullWidth}`}>
        <label className={styles.label} htmlFor="contact-notes">Notes</label>
        <textarea id="contact-notes" className={styles.textarea} value={form.notes} onChange={set('notes')} rows={2} />
      </div>
    </div>
  )
}
