import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router'
import { ApiClientError } from '../../types'
import { mapGroupedLinks } from '../../services/api'
import {
  useAllTags,
  useApplicationDetail,
  useApplicationMutations,
  useResumeList,
} from '../../hooks/queries'
import { LinksPanel } from '../../components/LinksPanel'
import Breadcrumb from '../../components/Breadcrumb'
import NotFound from '../../components/NotFound'
import { ConfirmDialog } from '../../components/ConfirmDialog'
import { useToast } from '../../components/toast'
import { LoadingSpinner } from '../../components/LoadingSpinner'
import { ApplicationPanel } from './ApplicationPanel'
import type { ApplicationPanelInput } from './ApplicationPanel'
import styles from './ApplicationDetailView.module.css'

export default function ApplicationDetailView() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()

  const numericId = id && /^\d+$/.test(id) ? Number(id) : null

  const [editing, setEditing] = useState(false)
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false)
  const { success, error } = useToast()

  useEffect(() => {
    if (numericId === null) {
      navigate('/applications', { replace: true })
    }
  }, [numericId, navigate])

  const detailQuery = useApplicationDetail(numericId ?? undefined)
  const resumesQuery = useResumeList()
  const tagsQuery = useAllTags()
  const { update, remove } = useApplicationMutations()

  const app = detailQuery.data ?? null
  const resumeVersions = resumesQuery.data ?? []
  const allTags = tagsQuery.data ?? []
  const errStatus = (detailQuery.error as ApiClientError | undefined)?.status
  const notFound = errStatus === 404
  const forbidden = errStatus === 403
  const loading = detailQuery.isPending

  useEffect(() => {
    if (detailQuery.isError && !notFound && !forbidden) {
      error('Failed to load application')
    }
  }, [detailQuery.isError, notFound, forbidden, error])

  const handleSave = async (data: ApplicationPanelInput) => {
    if (!app || numericId === null) return
    try {
      await update.mutateAsync({
        id: numericId,
        data: {
          company: data.company,
          position: data.position,
          status: data.status,
          url: data.url ?? null,
          description: data.description ?? undefined,
          notes: data.notes ?? undefined,
          tags: data.tags ?? [],
          resume_version_id: data.resume_version_id ?? null,
        },
      })
      setEditing(false)
      success('Saved')
    } catch {
      error('Failed to save')
    }
  }

  const handleDelete = async () => {
    if (numericId === null) return
    try {
      await remove.mutateAsync(numericId)
      success('Application deleted')
      navigate('/applications')
    } catch {
      error('Failed to delete application')
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

  return (
    <div className={styles.container} data-testid="application-detail-view">
      <Breadcrumb
        items={[
          { label: 'Applications', to: '/applications' },
          { label: `${app.company} — ${app.position}` },
        ]}
      />

      {editing ? (
        <ApplicationPanel
          key="edit"
          mode="edit"
          application={app}
          allTags={allTags}
          resumeVersions={resumeVersions}
          onSave={handleSave}
          onCancel={() => setEditing(false)}
          backTo="/applications"
        />
      ) : (
        <ApplicationPanel
          key="view"
          mode="view"
          application={app}
          resumeVersions={resumeVersions}
          onEdit={() => setEditing(true)}
          onDelete={() => setShowDeleteConfirm(true)}
          backTo="/applications"
        />
      )}

      <LinksPanel
        resourceType="application"
        resourceId={numericId}
        links={mapGroupedLinks(app.links as Record<string, unknown[]>)}
        onChange={() => detailQuery.refetch()}
      />

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
