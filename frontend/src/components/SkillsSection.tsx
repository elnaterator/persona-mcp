import { useState } from 'react'
import { Pencil, Trash2 } from 'lucide-react'
import type { Skill } from '../types/resume'
import { EntryForm, type FieldConfig } from './EntryForm'
import { ConfirmDialog } from './ConfirmDialog'
import { StatusMessage } from './StatusMessage'
import { addEntry, updateEntry, removeEntry, addVersionEntry, updateVersionEntry, removeVersionEntry } from '../services/api'
import styles from './SkillsSection.module.css'

interface SkillsSectionProps {
  skills: Skill[]
  onUpdate?: () => void
  versionId?: number
}

type Mode = 'view' | 'add' | { type: 'edit'; index: number } | { type: 'delete'; index: number }

const skillFields: FieldConfig[] = [
  { name: 'name', label: 'Skill Name', type: 'text', required: true },
  { name: 'category', label: 'Category', type: 'text', required: false },
]

export default function SkillsSection({ skills, onUpdate, versionId }: SkillsSectionProps) {
  const [mode, setMode] = useState<Mode>('view')
  const [statusMessage, setStatusMessage] = useState<{ type: 'success' | 'error'; message: string } | null>(null)

  const groupedSkills = skills.reduce((acc, skill, index) => {
    const category = skill.category || 'Other'
    if (!acc[category]) {
      acc[category] = []
    }
    acc[category].push({ ...skill, originalIndex: index })
    return acc
  }, {} as Record<string, Array<Skill & { originalIndex: number }>>)

  const categories = Object.keys(groupedSkills).sort()

  const handleAdd = async (data: Record<string, string | string[]>) => {
    try {
      const entryData: Skill = {
        name: data.name as string,
        category: (data.category as string) || null,
      }

      if (versionId !== undefined) {
        await addVersionEntry(versionId, 'skills', entryData)
      } else {
        await addEntry('skills', entryData)
      }
      setStatusMessage({ type: 'success', message: 'Skill added successfully' })
      setMode('view')
      if (onUpdate) onUpdate()
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Failed to add skill'
      setStatusMessage({ type: 'error', message: msg })
    }
  }

  const handleEdit = async (data: Record<string, string | string[]>) => {
    if (typeof mode !== 'object' || mode.type !== 'edit') return

    try {
      const entryData: Partial<Skill> = {
        name: data.name as string,
        category: (data.category as string) || null,
      }

      if (versionId !== undefined) {
        await updateVersionEntry(versionId, 'skills', mode.index, entryData)
      } else {
        await updateEntry('skills', mode.index, entryData)
      }
      setStatusMessage({ type: 'success', message: 'Skill updated successfully' })
      setMode('view')
      if (onUpdate) onUpdate()
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Failed to update skill'
      setStatusMessage({ type: 'error', message: msg })
    }
  }

  const handleDelete = async () => {
    if (typeof mode !== 'object' || mode.type !== 'delete') return

    try {
      if (versionId !== undefined) {
        await removeVersionEntry(versionId, 'skills', mode.index)
      } else {
        await removeEntry('skills', mode.index)
      }
      setStatusMessage({ type: 'success', message: 'Skill deleted successfully' })
      setMode('view')
      if (onUpdate) onUpdate()
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Failed to delete skill'
      setStatusMessage({ type: 'error', message: msg })
      setMode('view')
    }
  }

  return (
    <section className={styles.container} data-testid="skills-section">
      <h2 className={styles.sectionLabel}>Skills</h2>

      {statusMessage && (
        <StatusMessage
          type={statusMessage.type}
          message={statusMessage.message}
          onDismiss={() => setStatusMessage(null)}
        />
      )}

      {categories.length > 0 ? (
        <div className={styles.list}>
          {categories.map((category) => (
            <div key={category} className={styles.skillGroup}>
              <span className={styles.categoryLabel}>{category}</span>
              <div className={styles.skillItems}>
                {groupedSkills[category].map((skill) => (
                  <div key={skill.originalIndex} className={styles.skillItem}>
                    <span className={styles.skillName}>{skill.name}</span>
                    <div className={styles.skillActions}>
                      <button
                        className={styles.editButton}
                        onClick={() => setMode({ type: 'edit', index: skill.originalIndex })}
                        aria-label="Edit skill"
                      >
                        <Pencil size={12} />
                      </button>
                      <button
                        className={styles.deleteButton}
                        onClick={() => setMode({ type: 'delete', index: skill.originalIndex })}
                        aria-label="Delete skill"
                      >
                        <Trash2 size={12} />
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      ) : (
        <p className={styles.placeholder}>Click "Add Skill" to add skills</p>
      )}

      {typeof mode === 'object' && mode.type === 'edit' && (
        <EntryForm
          fields={skillFields}
          initialData={skills[mode.index] as unknown as Record<string, string | string[]>}
          onSubmit={handleEdit}
          onCancel={() => setMode('view')}
        />
      )}

      {mode === 'add' && (
        <EntryForm
          fields={skillFields}
          onSubmit={handleAdd}
          onCancel={() => setMode('view')}
        />
      )}

      {mode === 'view' && (
        <button className={styles.addButton} onClick={() => setMode('add')}>
          Add Skill
        </button>
      )}

      {typeof mode === 'object' && mode.type === 'delete' && (
        <ConfirmDialog
          message="Are you sure you want to delete this skill?"
          onConfirm={handleDelete}
          onCancel={() => setMode('view')}
        />
      )}
    </section>
  )
}
