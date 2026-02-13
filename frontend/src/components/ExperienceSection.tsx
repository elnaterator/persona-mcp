import { useState } from 'react'
import type { WorkExperience } from '../types/resume'
import { EntryForm, type FieldConfig } from './EntryForm'
import { ConfirmDialog } from './ConfirmDialog'
import { StatusMessage } from './StatusMessage'
import { addEntry, updateEntry, removeEntry } from '../services/api'
import styles from './ExperienceSection.module.css'

interface ExperienceSectionProps {
  experience: WorkExperience[]
  onUpdate?: () => void
}

type Mode = 'view' | 'add' | { type: 'edit'; index: number } | { type: 'delete'; index: number }

const experienceFields: FieldConfig[] = [
  { name: 'title', label: 'Title', type: 'text', required: true },
  { name: 'company', label: 'Company', type: 'text', required: true },
  { name: 'start_date', label: 'Start Date', type: 'text', required: false },
  { name: 'end_date', label: 'End Date', type: 'text', required: false },
  { name: 'location', label: 'Location', type: 'text', required: false },
  { name: 'highlights', label: 'Highlights', type: 'highlights', required: false },
]

export default function ExperienceSection({ experience, onUpdate }: ExperienceSectionProps) {
  const [mode, setMode] = useState<Mode>('view')
  const [statusMessage, setStatusMessage] = useState<{ type: 'success' | 'error'; message: string } | null>(null)

  const handleAdd = async (data: Record<string, string | string[]>) => {
    try {
      const entryData: WorkExperience = {
        title: data.title as string,
        company: data.company as string,
        start_date: (data.start_date as string) || null,
        end_date: (data.end_date as string) || null,
        location: (data.location as string) || null,
        highlights: (data.highlights as string[]) || [],
      }

      await addEntry('experience', entryData)
      setStatusMessage({ type: 'success', message: 'Experience added successfully' })
      setMode('view')
      if (onUpdate) onUpdate()
    } catch {
      setStatusMessage({ type: 'error', message: 'Failed to add experience' })
    }
  }

  const handleEdit = async (data: Record<string, string | string[]>) => {
    if (typeof mode !== 'object' || mode.type !== 'edit') return

    try {
      const entryData: Partial<WorkExperience> = {
        title: data.title as string,
        company: data.company as string,
        start_date: (data.start_date as string) || null,
        end_date: (data.end_date as string) || null,
        location: (data.location as string) || null,
        highlights: (data.highlights as string[]) || [],
      }

      await updateEntry('experience', mode.index, entryData)
      setStatusMessage({ type: 'success', message: 'Experience updated successfully' })
      setMode('view')
      if (onUpdate) onUpdate()
    } catch {
      setStatusMessage({ type: 'error', message: 'Failed to update experience' })
    }
  }

  const handleDelete = async () => {
    if (typeof mode !== 'object' || mode.type !== 'delete') return

    try {
      await removeEntry('experience', mode.index)
      setStatusMessage({ type: 'success', message: 'Experience deleted successfully' })
      setMode('view')
      if (onUpdate) onUpdate()
    } catch {
      setStatusMessage({ type: 'error', message: 'Failed to delete experience' })
      setMode('view')
    }
  }

  return (
    <section className={styles.container} data-testid="experience-section">
      <h2 className={styles.heading}>Work Experience</h2>

      {statusMessage && (
        <StatusMessage
          type={statusMessage.type}
          message={statusMessage.message}
          onDismiss={() => setStatusMessage(null)}
        />
      )}

      {mode === 'add' && (
        <EntryForm
          fields={experienceFields}
          onSubmit={handleAdd}
          onCancel={() => setMode('view')}
        />
      )}

      {typeof mode === 'object' && mode.type === 'edit' && (
        <EntryForm
          fields={experienceFields}
          initialData={experience[mode.index] as unknown as Record<string, string | string[]>}
          onSubmit={handleEdit}
          onCancel={() => setMode('view')}
        />
      )}

      {mode === 'view' && (
        <>
          {experience.length > 0 ? (
            <div className={styles.list}>
              {experience.map((entry, index) => (
                <div key={index} className={styles.entry}>
                  <div className={styles.header}>
                    <h3 className={styles.title}>{entry.title}</h3>
                    <span className={styles.company}>{entry.company}</span>
                  </div>
                  <div className={styles.metadata}>
                    {(entry.start_date || entry.end_date) && (
                      <span className={styles.dates}>
                        {entry.start_date || 'N/A'} – {entry.end_date || 'Present'}
                      </span>
                    )}
                    {entry.location && (
                      <span className={styles.location}>{entry.location}</span>
                    )}
                  </div>
                  {entry.highlights && entry.highlights.length > 0 && (
                    <ul className={styles.highlights}>
                      {entry.highlights.map((highlight, idx) => (
                        <li key={idx} className={styles.highlight}>
                          {highlight}
                        </li>
                      ))}
                    </ul>
                  )}
                  <div className={styles.entryActions}>
                    <button
                      className={styles.editButton}
                      onClick={() => setMode({ type: 'edit', index })}
                    >
                      Edit
                    </button>
                    <button
                      className={styles.deleteButton}
                      onClick={() => setMode({ type: 'delete', index })}
                    >
                      Delete
                    </button>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className={styles.empty}>No work experience listed.</p>
          )}

          <button className={styles.addButton} onClick={() => setMode('add')}>
            Add Experience
          </button>
        </>
      )}

      {typeof mode === 'object' && mode.type === 'delete' && (
        <ConfirmDialog
          message="Are you sure you want to delete this experience entry?"
          onConfirm={handleDelete}
          onCancel={() => setMode('view')}
        />
      )}
    </section>
  )
}
