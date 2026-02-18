import { useCallback, useEffect, useState } from 'react'
import type { ResumeVersion } from '../types/resume'
import { getResumeVersion, updateResumeLabel } from '../services/api'
import ContactSection from './ContactSection'
import SummarySection from './SummarySection'
import ExperienceSection from './ExperienceSection'
import EducationSection from './EducationSection'
import SkillsSection from './SkillsSection'
import { LoadingSpinner } from './LoadingSpinner'
import { StatusMessage } from './StatusMessage'
import styles from './ResumeDetailView.module.css'

interface ResumeDetailViewProps {
  versionId: number
  onBack: () => void
}

export default function ResumeDetailView({ versionId, onBack }: ResumeDetailViewProps) {
  const [version, setVersion] = useState<ResumeVersion | null>(null)
  const [loading, setLoading] = useState(true)
  const [statusMessage, setStatusMessage] = useState<{ type: 'success' | 'error'; message: string } | null>(null)
  const [editingLabel, setEditingLabel] = useState(false)
  const [labelInput, setLabelInput] = useState('')

  const load = useCallback(async () => {
    try {
      setLoading(true)
      const data = await getResumeVersion(versionId)
      setVersion(data)
      setLabelInput(data.label)
    } catch {
      setStatusMessage({ type: 'error', message: 'Failed to load resume version' })
    } finally {
      setLoading(false)
    }
  }, [versionId])

  useEffect(() => {
    load()
  }, [load])

  const handleLabelSave = async () => {
    if (!labelInput.trim()) return
    try {
      const updated = await updateResumeLabel(versionId, labelInput.trim())
      setVersion((prev) => prev ? { ...prev, label: updated.label } : prev)
      setEditingLabel(false)
    } catch {
      setStatusMessage({ type: 'error', message: 'Failed to update label' })
    }
  }

  if (loading) return <LoadingSpinner />
  if (!version) return null

  const resume = version.resume_data

  return (
    <div className={styles.container} data-testid="resume-detail-view">
      <div className={styles.topBar}>
        <button className={styles.backButton} onClick={onBack}>
          Back to list
        </button>
        {version.is_default && (
          <span className={styles.defaultBadge}>Default</span>
        )}
      </div>

      <div className={styles.labelRow}>
        {editingLabel ? (
          <div className={styles.labelEdit}>
            <input
              className={styles.labelInput}
              value={labelInput}
              onChange={(e) => setLabelInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter') handleLabelSave()
                if (e.key === 'Escape') setEditingLabel(false)
              }}
              autoFocus
            />
            <button className={styles.saveLabel} onClick={handleLabelSave}>
              Save
            </button>
            <button className={styles.cancelLabel} onClick={() => setEditingLabel(false)}>
              Cancel
            </button>
          </div>
        ) : (
          <div className={styles.labelDisplay}>
            <h2 className={styles.label}>{version.label}</h2>
            <button className={styles.editLabelBtn} onClick={() => setEditingLabel(true)}>
              Rename
            </button>
          </div>
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
        <ContactSection
          contact={resume.contact}
          onUpdate={load}
          versionId={versionId}
        />
        <SummarySection
          summary={resume.summary}
          onUpdate={load}
          versionId={versionId}
        />
        <ExperienceSection
          experience={resume.experience}
          onUpdate={load}
          versionId={versionId}
        />
        <EducationSection
          education={resume.education}
          onUpdate={load}
          versionId={versionId}
        />
        <SkillsSection
          skills={resume.skills}
          onUpdate={load}
          versionId={versionId}
        />
      </div>
    </div>
  )
}
