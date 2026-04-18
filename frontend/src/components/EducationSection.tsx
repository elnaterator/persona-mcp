import { useState } from 'react'
import { Pencil, Trash2 } from 'lucide-react'
import type { Education } from '../types/resume'
import { EntryForm, type FieldConfig } from './EntryForm'
import { ConfirmDialog } from './ConfirmDialog'
import { StatusMessage } from './StatusMessage'
import { addEntry, updateEntry, removeEntry, addVersionEntry, updateVersionEntry, removeVersionEntry } from '../services/api'
import styles from './EducationSection.module.css'

interface EducationSectionProps {
  education: Education[]
  onUpdate?: () => void
  versionId?: number
}

type Mode = 'view' | 'add' | { type: 'edit'; index: number } | { type: 'delete'; index: number }

const educationFields: FieldConfig[] = [
  { name: 'degree', label: 'Degree', type: 'text', required: true, group: 'title', placeholder: 'Degree' },
  { name: 'field', label: 'Field of Study', type: 'text', required: false, group: 'title', placeholder: 'Field of Study' },
  { name: 'institution', label: 'Institution', type: 'text', required: true, group: 'meta', placeholder: 'Institution' },
  { name: 'start_date', label: 'Start Date', type: 'text', required: false, group: 'meta', placeholder: 'Start Date' },
  { name: 'end_date', label: 'End Date', type: 'text', required: false, group: 'meta', placeholder: 'End Date' },
  { name: 'honors', label: 'Honors', type: 'text', required: false, group: 'meta', placeholder: 'Honors' },
  { name: 'highlights', label: 'Highlights', type: 'highlights', required: false },
]

export default function EducationSection({ education, onUpdate, versionId }: EducationSectionProps) {
  const [mode, setMode] = useState<Mode>('view')
  const [statusMessage, setStatusMessage] = useState<{ type: 'success' | 'error'; message: string } | null>(null)

  const handleAdd = async (data: Record<string, string | string[]>) => {
    try {
      const entryData: Education = {
        institution: data.institution as string,
        degree: data.degree as string,
        field: (data.field as string) || null,
        start_date: (data.start_date as string) || null,
        end_date: (data.end_date as string) || null,
        honors: (data.honors as string) || null,
        highlights: (data.highlights as string[]) || [],
      }

      if (versionId !== undefined) {
        await addVersionEntry(versionId, 'education', entryData)
      } else {
        await addEntry('education', entryData)
      }
      setStatusMessage({ type: 'success', message: 'Education added successfully' })
      setMode('view')
      if (onUpdate) onUpdate()
    } catch {
      setStatusMessage({ type: 'error', message: 'Failed to add education' })
    }
  }

  const handleEdit = async (data: Record<string, string | string[]>) => {
    if (typeof mode !== 'object' || mode.type !== 'edit') return

    try {
      const entryData: Partial<Education> = {
        institution: data.institution as string,
        degree: data.degree as string,
        field: (data.field as string) || null,
        start_date: (data.start_date as string) || null,
        end_date: (data.end_date as string) || null,
        honors: (data.honors as string) || null,
        highlights: (data.highlights as string[]) || [],
      }

      if (versionId !== undefined) {
        await updateVersionEntry(versionId, 'education', mode.index, entryData)
      } else {
        await updateEntry('education', mode.index, entryData)
      }
      setStatusMessage({ type: 'success', message: 'Education updated successfully' })
      setMode('view')
      if (onUpdate) onUpdate()
    } catch {
      setStatusMessage({ type: 'error', message: 'Failed to update education' })
    }
  }

  const handleDelete = async () => {
    if (typeof mode !== 'object' || mode.type !== 'delete') return

    try {
      if (versionId !== undefined) {
        await removeVersionEntry(versionId, 'education', mode.index)
      } else {
        await removeEntry('education', mode.index)
      }
      setStatusMessage({ type: 'success', message: 'Education deleted successfully' })
      setMode('view')
      if (onUpdate) onUpdate()
    } catch {
      setStatusMessage({ type: 'error', message: 'Failed to delete education' })
      setMode('view')
    }
  }

  return (
    <section className={styles.container} data-testid="education-section">
      <h2 className={styles.sectionLabel}>Education</h2>

      {statusMessage && (
        <StatusMessage
          type={statusMessage.type}
          message={statusMessage.message}
          onDismiss={() => setStatusMessage(null)}
        />
      )}

      {education.length > 0 ? (
        <div className={styles.list}>
          {education.map((entry, index) => (
            typeof mode === 'object' && mode.type === 'edit' && mode.index === index ? (
              <EntryForm
                key={index}
                fields={educationFields}
                initialData={entry as unknown as Record<string, string | string[]>}
                onSubmit={handleEdit}
                onCancel={() => setMode('view')}
              />
            ) : (
              <div key={index} className={styles.entry}>
                <div className={styles.entryHeader}>
                  <div className={styles.entryInfo}>
                    <span className={styles.entryDegree}>
                      {entry.degree}{entry.field ? `, ${entry.field}` : ''}
                    </span>
                    <span className={styles.entryMeta}>
                      {entry.institution}
                      {(entry.start_date || entry.end_date) && (
                        <span className={styles.entryDates}>
                          {' · '}{entry.start_date || 'N/A'} – {entry.end_date || 'N/A'}
                        </span>
                      )}
                      {entry.honors && (
                        <span className={styles.entryHonors}>{' · '}{entry.honors}</span>
                      )}
                    </span>
                  </div>
                  <div className={styles.entryActions}>
                    <button
                      className={styles.editButton}
                      onClick={() => setMode({ type: 'edit', index })}
                      aria-label="Edit education"
                    >
                      <Pencil size={13} />
                    </button>
                    <button
                      className={styles.deleteButton}
                      onClick={() => setMode({ type: 'delete', index })}
                      aria-label="Delete education"
                    >
                      <Trash2 size={13} />
                    </button>
                  </div>
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
              </div>
            )
          ))}
        </div>
      ) : (
        mode !== 'add' && <p className={styles.placeholder}>Click "Add Education" to add education history</p>
      )}

      {mode === 'add' && (
        <EntryForm
          fields={educationFields}
          onSubmit={handleAdd}
          onCancel={() => setMode('view')}
        />
      )}

      {mode === 'view' && (
        <button className={styles.addButton} onClick={() => setMode('add')}>
          Add Education
        </button>
      )}

      {typeof mode === 'object' && mode.type === 'delete' && (
        <ConfirmDialog
          message="Are you sure you want to delete this education entry?"
          onConfirm={handleDelete}
          onCancel={() => setMode('view')}
        />
      )}
    </section>
  )
}
