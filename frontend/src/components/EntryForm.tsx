import { useState, FormEvent } from 'react'
import styles from './EntryForm.module.css'

export interface FieldConfig {
  name: string
  label: string
  type: 'text' | 'textarea' | 'highlights'
  required: boolean
}

interface EntryFormProps {
  fields: FieldConfig[]
  initialData?: Record<string, string | string[]>
  onSubmit: (data: Record<string, string | string[]>) => void
  onCancel: () => void
}

export function EntryForm({ fields, initialData = {}, onSubmit, onCancel }: EntryFormProps) {
  const [formData, setFormData] = useState<Record<string, string | string[]>>(() => {
    const data: Record<string, string | string[]> = {}
    fields.forEach((field) => {
      if (field.type === 'highlights') {
        data[field.name] = initialData[field.name] || []
      } else {
        data[field.name] = (initialData[field.name] as string) || ''
      }
    })
    return data
  })

  const [errors, setErrors] = useState<Record<string, string>>({})

  const handleInputChange = (name: string, value: string) => {
    setFormData((prev) => ({ ...prev, [name]: value }))
    if (errors[name]) {
      setErrors((prev) => {
        const newErrors = { ...prev }
        delete newErrors[name]
        return newErrors
      })
    }
  }

  const handleHighlightsChange = (index: number, value: string) => {
    const fieldName = fields.find((f) => f.type === 'highlights')?.name
    if (!fieldName) return

    setFormData((prev) => {
      const highlights = [...(prev[fieldName] as string[])]
      highlights[index] = value
      return { ...prev, [fieldName]: highlights }
    })
  }

  const addHighlight = () => {
    const fieldName = fields.find((f) => f.type === 'highlights')?.name
    if (!fieldName) return

    setFormData((prev) => {
      const highlights = [...(prev[fieldName] as string[])]
      highlights.push('')
      return { ...prev, [fieldName]: highlights }
    })
  }

  const removeHighlight = (index: number) => {
    const fieldName = fields.find((f) => f.type === 'highlights')?.name
    if (!fieldName) return

    setFormData((prev) => {
      const highlights = [...(prev[fieldName] as string[])]
      highlights.splice(index, 1)
      return { ...prev, [fieldName]: highlights }
    })
  }

  const validate = (): boolean => {
    const newErrors: Record<string, string> = {}

    fields.forEach((field) => {
      if (field.required && field.type !== 'highlights') {
        const value = formData[field.name] as string
        if (!value || value.trim() === '') {
          newErrors[field.name] = `${field.label} is required`
        }
      }
    })

    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault()

    if (!validate()) {
      return
    }

    onSubmit(formData)
  }

  return (
    <form className={styles.form} onSubmit={handleSubmit}>
      {fields.map((field) => {
        if (field.type === 'highlights') {
          const highlights = (formData[field.name] as string[]) || []

          return (
            <div key={field.name} className={styles.fieldGroup}>
              <label className={styles.label}>
                {field.label}
                {field.required && <span className={styles.required}>*</span>}
              </label>
              <div className={styles.highlightsList}>
                {highlights.map((highlight, index) => (
                  <div key={index} className={styles.highlightItem}>
                    <input
                      type="text"
                      className={styles.input}
                      placeholder="Highlight"
                      value={highlight}
                      onChange={(e) => handleHighlightsChange(index, e.target.value)}
                    />
                    <button
                      type="button"
                      className={styles.removeButton}
                      onClick={() => removeHighlight(index)}
                      aria-label="Remove"
                    >
                      Remove
                    </button>
                  </div>
                ))}
                <button
                  type="button"
                  className={styles.addButton}
                  onClick={addHighlight}
                  aria-label="Add highlight"
                >
                  Add Highlight
                </button>
              </div>
            </div>
          )
        }

        if (field.type === 'textarea') {
          return (
            <div key={field.name} className={styles.fieldGroup}>
              <label htmlFor={field.name} className={styles.label}>
                {field.label}
                {field.required && <span className={styles.required}>*</span>}
              </label>
              <textarea
                id={field.name}
                className={styles.textarea}
                value={formData[field.name] as string}
                onChange={(e) => handleInputChange(field.name, e.target.value)}
                rows={10}
                maxLength={5000}
              />
              {errors[field.name] && (
                <span className={styles.error}>{errors[field.name]}</span>
              )}
            </div>
          )
        }

        return (
          <div key={field.name} className={styles.fieldGroup}>
            <label htmlFor={field.name} className={styles.label}>
              {field.label}
              {field.required && <span className={styles.required}>*</span>}
            </label>
            <input
              type="text"
              id={field.name}
              className={styles.input}
              value={formData[field.name] as string}
              onChange={(e) => handleInputChange(field.name, e.target.value)}
            />
            {errors[field.name] && (
              <span className={styles.error}>{errors[field.name]}</span>
            )}
          </div>
        )
      })}

      <div className={styles.actions}>
        <button type="button" className={styles.cancelButton} onClick={onCancel}>
          Cancel
        </button>
        <button type="submit" className={styles.saveButton}>
          Save
        </button>
      </div>
    </form>
  )
}
