import { useCallback, useEffect, useState } from 'react'
import { useParams, useNavigate, Link } from 'react-router'
import { Pencil, Trash2, Check, X } from 'lucide-react'
import type { Application, ResumeVersionSummary } from '../types/resume'
import {
  getApplication,
  updateApplication,
  deleteApplication,
  listResumes,
} from '../services/api'
import ContactsPanel from './ContactsPanel'
import CommunicationsPanel from './CommunicationsPanel'
import Breadcrumb from './Breadcrumb'
import NotFound from './NotFound'
import { ConfirmDialog } from './ConfirmDialog'
import { StatusMessage } from './StatusMessage'
import { LoadingSpinner } from './LoadingSpinner'
import { SectionCard } from './SectionCard'
import { MarkdownContent } from './MarkdownContent'
import { AutoResizeTextarea } from './AutoResizeTextarea'
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

const STATUS_COLORS: Record<string, { bg: string; color: string }> = {
  Interested:     { bg: 'rgba(136,136,220,0.12)', color: '#9898d8' },
  Applied:        { bg: 'rgba(86,156,214,0.12)',  color: '#76c0f0' },
  'Phone Screen': { bg: 'rgba(220,180,80,0.12)',  color: '#d4b060' },
  Interview:      { bg: 'rgba(180,120,220,0.12)', color: '#c080e0' },
  Offer:          { bg: 'rgba(82,183,136,0.12)',  color: '#52b788' },
  Rejected:       { bg: 'rgba(255,68,68,0.10)',   color: '#ff6868' },
  Withdrawn:      { bg: 'rgba(120,120,120,0.10)', color: '#888888' },
  Accepted:       { bg: 'rgba(82,183,136,0.22)',  color: '#52b788' },
}

type EditSection = 'details' | 'description' | 'notes' | 'resume' | null

export default function ApplicationDetailView() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()

  const numericId = id && /^\d+$/.test(id) ? Number(id) : null

  const [app, setApp] = useState<Application | null>(null)
  const [resumeVersions, setResumeVersions] = useState<ResumeVersionSummary[]>([])
  const [notFound, setNotFound] = useState(false)
  const [forbidden, setForbidden] = useState(false)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [editingSection, setEditingSection] = useState<EditSection>(null)
  const [sectionForm, setSectionForm] = useState<Partial<Application>>({})
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false)
  const [statusMessage, setStatusMessage] = useState<{ type: 'success' | 'error'; message: string } | null>(null)

  useEffect(() => {
    if (numericId === null) {
      navigate('/applications', { replace: true })
    }
  }, [numericId, navigate])

  const load = useCallback(async () => {
    if (numericId === null) return
    try {
      setLoading(true)
      const [appData, versions] = await Promise.all([
        getApplication(numericId),
        listResumes(),
      ])
      setApp(appData)
      setResumeVersions(versions)
    } catch (err: unknown) {
      const status = (err as { status?: number })?.status
      if (status === 404) {
        setNotFound(true)
      } else if (status === 403) {
        setForbidden(true)
      } else {
        setStatusMessage({ type: 'error', message: 'Failed to load application' })
      }
    } finally {
      setLoading(false)
    }
  }, [numericId])

  useEffect(() => {
    load()
  }, [load])

  const startEdit = (section: EditSection) => {
    if (!app) return
    setSectionForm({ ...app })
    setEditingSection(section)
  }

  const cancelEdit = () => {
    setEditingSection(null)
    setSectionForm({})
  }

  const saveSection = async () => {
    if (!app || numericId === null) return
    if (!sectionForm.company?.trim() || !sectionForm.position?.trim()) return
    try {
      setSaving(true)
      const updated = await updateApplication(numericId, {
        company: sectionForm.company?.trim() ?? app.company,
        position: sectionForm.position?.trim() ?? app.position,
        status: sectionForm.status ?? app.status,
        url: sectionForm.url?.trim() || null,
        description: sectionForm.description?.trim() ?? app.description,
        notes: sectionForm.notes?.trim() ?? app.notes,
        resume_version_id: 'resume_version_id' in sectionForm
          ? sectionForm.resume_version_id ?? null
          : app.resume_version_id,
      })
      setApp(updated)
      setEditingSection(null)
      setSectionForm({})
      setStatusMessage({ type: 'success', message: 'Saved' })
    } catch {
      setStatusMessage({ type: 'error', message: 'Failed to save' })
    } finally {
      setSaving(false)
    }
  }

  const setField =
    (field: keyof Application) =>
    (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
      setSectionForm((prev) => ({ ...prev, [field]: e.target.value }))
    }

  const setFieldValue =
    (field: keyof Application) =>
    (value: string) => {
      setSectionForm((prev) => ({ ...prev, [field]: value }))
    }

  const handleDelete = async () => {
    if (numericId === null) return
    try {
      await deleteApplication(numericId)
      navigate('/applications')
    } catch {
      setStatusMessage({ type: 'error', message: 'Failed to delete application' })
      setShowDeleteConfirm(false)
    }
  }

  if (numericId === null) return null
  if (loading) return <LoadingSpinner />
  if (notFound)
    return (
      <NotFound
        entityName="Application"
        backTo="/applications"
        backLabel="Back to Applications"
      />
    )
  if (forbidden)
    return (
      <NotFound
        entityName="Application"
        backTo="/applications"
        backLabel="Back to Applications"
        heading="This application isn't yours"
        message="This application belongs to another account and cannot be accessed."
      />
    )
  if (!app) return null

  const statusStyle = STATUS_COLORS[app.status] ?? { bg: 'rgba(120,120,120,0.10)', color: '#888888' }
  const linkedResume = resumeVersions.find((rv) => rv.id === app.resume_version_id)

  return (
    <div className={styles.container} data-testid="application-detail-view">
      <Breadcrumb
        items={[
          { label: 'Applications', to: '/applications' },
          { label: `${app.company} — ${app.position}` },
        ]}
      />

      <div className={styles.topBar}>
        <Link to="/applications" className={styles.backButton}>
          Back
        </Link>
        <h2 className={styles.topBarTitle}>{app.company} — {app.position}</h2>
        <div className={styles.topBarActions}>
          <button className={styles.deleteButton} onClick={() => setShowDeleteConfirm(true)} aria-label="Delete application">
            <Trash2 size={14} />
          </button>
        </div>
      </div>

      <div className={styles.meta}>
        <span
          className={styles.statusBadge}
          style={{ background: statusStyle.bg, color: statusStyle.color }}
        >
          {app.status}
        </span>
        {app.url && (
          <a
            href={app.url}
            className={styles.urlLink}
            target="_blank"
            rel="noopener noreferrer"
          >
            {app.url}
          </a>
        )}
      </div>

      {statusMessage && (
        <StatusMessage
          type={statusMessage.type}
          message={statusMessage.message}
          onDismiss={() => setStatusMessage(null)}
        />
      )}

      <div className={styles.sections}>
      {/* Details section */}
      <SectionCard
        label="Details"
        action={editingSection === 'details' ? (
          <div className={styles.sectionActions}>
            <button className={styles.saveIconButton} onClick={saveSection} disabled={saving || !sectionForm.company?.trim() || !sectionForm.position?.trim()} aria-label="Save">
              <Check size={14} />
            </button>
            <button className={styles.cancelIconButton} onClick={cancelEdit} aria-label="Cancel">
              <X size={14} />
            </button>
          </div>
        ) : (
          <button className={styles.editButton} onClick={() => startEdit('details')} aria-label="Edit details">
            <Pencil size={14} />
          </button>
        )}
      >
        {editingSection === 'details' ? (
          <div className={styles.sectionForm}>
            <div className={styles.formRow}>
              <div className={styles.formField}>
                <label className={styles.formLabel} htmlFor="det-company">Company *</label>
                <input
                  id="det-company"
                  className={styles.input}
                  value={sectionForm.company ?? ''}
                  onChange={setField('company')}
                  placeholder="Company name"
                />
              </div>
              <div className={styles.formField}>
                <label className={styles.formLabel} htmlFor="det-position">Position *</label>
                <input
                  id="det-position"
                  className={styles.input}
                  value={sectionForm.position ?? ''}
                  onChange={setField('position')}
                  placeholder="Job title"
                />
              </div>
            </div>
            <div className={styles.formRow}>
              <div className={styles.formField}>
                <label className={styles.formLabel} htmlFor="det-status">Status</label>
                <select
                  id="det-status"
                  className={styles.select}
                  value={sectionForm.status ?? 'Interested'}
                  onChange={setField('status')}
                >
                  {ALL_STATUSES.map((s) => (
                    <option key={s} value={s}>{s}</option>
                  ))}
                </select>
              </div>
              <div className={styles.formField}>
                <label className={styles.formLabel} htmlFor="det-url">URL</label>
                <input
                  id="det-url"
                  type="url"
                  className={styles.input}
                  value={sectionForm.url ?? ''}
                  onChange={setField('url')}
                  placeholder="https://..."
                />
              </div>
            </div>
          </div>
        ) : (
          <dl className={styles.fieldList}>
            <div className={styles.fieldRow}>
              <dt className={styles.fieldKey}>Company</dt>
              <dd className={styles.fieldVal}>{app.company}</dd>
            </div>
            <div className={styles.fieldRow}>
              <dt className={styles.fieldKey}>Position</dt>
              <dd className={styles.fieldVal}>{app.position}</dd>
            </div>
            <div className={styles.fieldRow}>
              <dt className={styles.fieldKey}>Status</dt>
              <dd className={styles.fieldVal}>
                <span
                  className={styles.statusBadgeInline}
                  style={{ background: statusStyle.bg, color: statusStyle.color }}
                >
                  {app.status}
                </span>
              </dd>
            </div>
            <div className={styles.fieldRow}>
              <dt className={styles.fieldKey}>URL</dt>
              <dd className={styles.fieldVal}>
                {app.url ? (
                  <a
                    href={app.url}
                    className={styles.urlLink}
                    target="_blank"
                    rel="noopener noreferrer"
                  >
                    {app.url}
                  </a>
                ) : (
                  <span className={styles.emptyText}>—</span>
                )}
              </dd>
            </div>
          </dl>
        )}
      </SectionCard>

      {/* Description section */}
      <SectionCard
        label="Description"
        action={editingSection === 'description' ? (
          <div className={styles.sectionActions}>
            <button className={styles.saveIconButton} onClick={saveSection} disabled={saving} aria-label="Save">
              <Check size={14} />
            </button>
            <button className={styles.cancelIconButton} onClick={cancelEdit} aria-label="Cancel">
              <X size={14} />
            </button>
          </div>
        ) : (
          <button className={styles.editButton} onClick={() => startEdit('description')} aria-label="Edit description">
            <Pencil size={14} />
          </button>
        )}
      >
        {editingSection === 'description' ? (
          <div className={styles.sectionForm}>
            <AutoResizeTextarea
              className={styles.textarea}
              value={sectionForm.description ?? ''}
              onChange={setFieldValue('description')}
              placeholder="Job description, requirements…"
            />
          </div>
        ) : app.description ? (
          <MarkdownContent>{app.description}</MarkdownContent>
        ) : (
          <p className={styles.emptyText}>Job description, requirements…</p>
        )}
      </SectionCard>

      {/* Notes section */}
      <SectionCard
        label="Notes"
        action={editingSection === 'notes' ? (
          <div className={styles.sectionActions}>
            <button className={styles.saveIconButton} onClick={saveSection} disabled={saving} aria-label="Save">
              <Check size={14} />
            </button>
            <button className={styles.cancelIconButton} onClick={cancelEdit} aria-label="Cancel">
              <X size={14} />
            </button>
          </div>
        ) : (
          <button className={styles.editButton} onClick={() => startEdit('notes')} aria-label="Edit notes">
            <Pencil size={14} />
          </button>
        )}
      >
        {editingSection === 'notes' ? (
          <div className={styles.sectionForm}>
            <AutoResizeTextarea
              className={styles.textarea}
              value={sectionForm.notes ?? ''}
              onChange={setFieldValue('notes')}
              placeholder="Personal notes…"
            />
          </div>
        ) : app.notes ? (
          <MarkdownContent>{app.notes}</MarkdownContent>
        ) : (
          <p className={styles.emptyText}>Personal notes…</p>
        )}
      </SectionCard>

      {/* Resume section */}
      <SectionCard
        label="Resume"
        action={editingSection === 'resume' ? (
          <div className={styles.sectionActions}>
            <button className={styles.saveIconButton} onClick={saveSection} disabled={saving} aria-label="Save">
              <Check size={14} />
            </button>
            <button className={styles.cancelIconButton} onClick={cancelEdit} aria-label="Cancel">
              <X size={14} />
            </button>
          </div>
        ) : (
          <button className={styles.editButton} onClick={() => startEdit('resume')} aria-label="Edit resume">
            <Pencil size={14} />
          </button>
        )}
      >
        {editingSection === 'resume' ? (
          <div className={styles.sectionForm}>
            <select
              className={styles.select}
              value={sectionForm.resume_version_id ?? ''}
              onChange={(e) =>
                setSectionForm((prev) => ({
                  ...prev,
                  resume_version_id: e.target.value ? Number(e.target.value) : null,
                }))
              }
            >
              <option value="">— None —</option>
              {resumeVersions.map((rv) => (
                <option key={rv.id} value={rv.id}>
                  {rv.label}{rv.is_default ? ' (default)' : ''}
                </option>
              ))}
            </select>
          </div>
        ) : linkedResume ? (
          <p className={styles.bodyText}>
            {linkedResume.label}{linkedResume.is_default ? ' (default)' : ''}
          </p>
        ) : (
          <p className={styles.emptyText}>No resume linked</p>
        )}
      </SectionCard>
      </div>

      <div className={styles.panels}>
        <ContactsPanel appId={numericId} />
        <CommunicationsPanel appId={numericId} />
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
