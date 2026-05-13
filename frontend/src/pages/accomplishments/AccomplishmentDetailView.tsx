import { useState, useEffect } from 'react'
import { useParams, useNavigate, Link } from 'react-router'
import { Pencil, Trash2, Check, X } from 'lucide-react'
import type { Accomplishment } from '../../types'
import { ApiClientError } from '../../types'
import { mapGroupedLinks } from '../../services/api'
import {
  useAccomplishmentDetail,
  useAccomplishmentMutations,
  useAllTags,
} from '../../hooks/queries'
import { LinksPanel } from '../../components/LinksPanel'
import Breadcrumb from '../../components/Breadcrumb'
import NotFound from '../../components/NotFound'
import { ConfirmDialog } from '../../components/ConfirmDialog'
import { TagInput } from '../../components/TagInput'
import { StatusMessage } from '../../components/StatusMessage'
import { SectionCard } from '../../components/SectionCard'
import { MarkdownContent } from '../../components/MarkdownContent'
import { AutoResizeTextarea } from '../../components/AutoResizeTextarea'
import styles from './AccomplishmentDetailView.module.css'

export default function AccomplishmentDetailView() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()

  const numericId = id && /^\d+$/.test(id) ? Number(id) : null

  const [editing, setEditing] = useState(false)
  const [editForm, setEditForm] = useState<Partial<Accomplishment>>({})
  const [editError, setEditError] = useState('')
  const [confirmDelete, setConfirmDelete] = useState(false)
  const [statusMessage, setStatusMessage] = useState<{ type: 'success' | 'error'; message: string } | null>(null)

  useEffect(() => {
    if (numericId === null) {
      navigate('/accomplishments', { replace: true })
    }
  }, [numericId, navigate])

  const detailQuery = useAccomplishmentDetail(numericId ?? undefined)
  const tagsQuery = useAllTags()
  const { update, remove } = useAccomplishmentMutations()

  const acc = detailQuery.data ?? null
  const allTags = tagsQuery.data ?? []
  const errStatus = (detailQuery.error as ApiClientError | undefined)?.status
  const notFound = errStatus === 404
  const forbidden = errStatus === 403
  const saving = update.isPending

  if (numericId === null) return null
  if (notFound) return <NotFound entityName="Accomplishment" backTo="/accomplishments" backLabel="Back to Accomplishments" />
  if (forbidden) return <NotFound entityName="Accomplishment" backTo="/accomplishments" backLabel="Back to Accomplishments" heading="This accomplishment isn't yours" message="This accomplishment belongs to another account and cannot be accessed." />
  if (!acc) {
    return <div>Loading…</div>
  }

  const startEdit = () => {
    setEditForm({
      title: acc.title,
      situation: acc.situation,
      task: acc.task,
      action: acc.action,
      result: acc.result,
      accomplishment_date: acc.accomplishment_date ?? '',
      tags: acc.tags,
    })
    setEditError('')
    setEditing(true)
  }

  const handleEditFieldChange = (field: keyof Accomplishment, value: string | string[]) => {
    setEditForm((prev) => ({ ...prev, [field]: value }))
  }

  const handleSave = async () => {
    if (!editForm.title?.trim()) {
      setEditError('Title is required')
      return
    }
    setEditError('')
    try {
      await update.mutateAsync({
        id: numericId,
        data: {
          ...editForm,
          accomplishment_date: editForm.accomplishment_date || null,
          tags: editForm.tags as string[],
        },
      })
      setEditing(false)
      setStatusMessage({ type: 'success', message: 'Saved' })
    } catch (err) {
      setEditError(err instanceof Error ? err.message : 'Failed to save')
    }
  }

  const handleDelete = async () => {
    try {
      await remove.mutateAsync(numericId)
      navigate('/accomplishments')
    } catch {
      setConfirmDelete(false)
      setStatusMessage({ type: 'error', message: 'Failed to delete accomplishment' })
    }
  }

  const STAR_FIELDS: { key: keyof Accomplishment; label: string; placeholder: string }[] = [
    { key: 'situation', label: 'Situation', placeholder: 'Describe the context or background…' },
    { key: 'task', label: 'Task', placeholder: 'What was your specific responsibility or goal?' },
    { key: 'action', label: 'Action', placeholder: 'What steps did you take to address the situation?' },
    { key: 'result', label: 'Result', placeholder: 'What was the outcome or impact? Include metrics where possible.' },
  ]

  return (
    <div className={styles.container}>
      <Breadcrumb
        items={[
          { label: 'Accomplishments', to: '/accomplishments' },
          { label: acc.title },
        ]}
      />

      <div className={styles.topBar}>
        <Link to="/accomplishments" className={styles.backButton}>Back</Link>
        {editing ? (
          <input
            className={styles.titleInput}
            type="text"
            value={editForm.title ?? ''}
            onChange={(e) => handleEditFieldChange('title', e.target.value)}
            autoFocus
          />
        ) : (
          <h2 className={styles.topBarTitle}>{acc.title}</h2>
        )}
        <div className={styles.topBarActions}>
          {editing ? (
            <>
              <button
                className={styles.saveIconButton}
                onClick={handleSave}
                disabled={saving}
                aria-label="Save accomplishment"
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
              <button className={styles.editButton} onClick={startEdit} aria-label="Edit accomplishment">
                <Pencil size={14} />
              </button>
              <button className={styles.deleteButton} onClick={() => setConfirmDelete(true)} aria-label="Delete accomplishment">
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
        <div className={styles.metaEdit}>
          <div className={styles.metaField}>
            <label className={styles.metaLabel} htmlFor="edit-tags">Tags</label>
            <TagInput
              id="edit-tags"
              value={(editForm.tags as string[]) ?? []}
              onChange={(tags) => handleEditFieldChange('tags', tags)}
              availableTags={allTags}
              allowCreate={true}
            />
          </div>
          <div className={`${styles.metaField} ${styles.metaFieldDate}`}>
            <label className={styles.metaLabel} htmlFor="edit-date">Date</label>
            <input
              id="edit-date"
              className={styles.metaInput}
              type="date"
              value={(editForm.accomplishment_date as string) ?? ''}
              onChange={(e) => handleEditFieldChange('accomplishment_date', e.target.value)}
            />
          </div>
        </div>
      ) : (
        (acc.accomplishment_date || acc.tags.length > 0) && (
          <div className={styles.meta}>
            {acc.tags.length > 0 && (
              <div className={styles.tagList}>
                {acc.tags.map((tag) => (
                  <span key={tag} className={styles.tagBadge}>{tag}</span>
                ))}
              </div>
            )}
            {acc.accomplishment_date && (
              <span className={styles.accomplishmentDate}>Accomplished {acc.accomplishment_date}</span>
            )}
          </div>
        )
      )}

      <div className={styles.starSections}>
        {STAR_FIELDS.map(({ key, label, placeholder }) => (
          <SectionCard key={key} label={label}>
            {editing ? (
              <AutoResizeTextarea
                className={styles.sectionTextarea}
                value={(editForm[key] as string) ?? ''}
                onChange={(value) => handleEditFieldChange(key, value)}
                placeholder={placeholder}
              />
            ) : (
              acc[key] ? (
                <MarkdownContent>{acc[key] as string}</MarkdownContent>
              ) : (
                <p className={styles.placeholderText}>{placeholder}</p>
              )
            )}
          </SectionCard>
        ))}
      </div>

      <LinksPanel
        resourceType="accomplishment"
        resourceId={numericId}
        links={mapGroupedLinks(acc.links as Record<string, unknown[]>)}
        onChange={() => detailQuery.refetch()}
      />

      {confirmDelete && (
        <ConfirmDialog
          message="Delete this accomplishment? This cannot be undone."
          onConfirm={handleDelete}
          onCancel={() => setConfirmDelete(false)}
        />
      )}
    </div>
  )
}
