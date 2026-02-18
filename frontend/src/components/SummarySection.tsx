import { useState } from 'react';
import { EditableSection } from './EditableSection';
import { updateSummary, updateVersionSummary } from '../services/api';
import styles from './SummarySection.module.css';

interface SummarySectionProps {
  summary: string;
  onUpdate?: () => void;
  versionId?: number;
}

export default function SummarySection({ summary, onUpdate, versionId }: SummarySectionProps) {
  const [formData, setFormData] = useState<string>(summary);
  const [validationError, setValidationError] = useState<string | null>(null);

  const handleSave = async () => {
    if (!formData.trim()) {
      setValidationError('Summary cannot be empty');
      throw new Error('Summary cannot be empty');
    }

    setValidationError(null);
    if (versionId !== undefined) {
      await updateVersionSummary(versionId, formData);
    } else {
      await updateSummary(formData);
    }
    if (onUpdate) {
      onUpdate();
    }
  };

  const handleChange = (value: string) => {
    setFormData(value);
    if (validationError) {
      setValidationError(null);
    }
  };

  if (!onUpdate) {
    return (
      <section className={styles.container} data-testid="summary-section">
        <h2 className={styles.heading}>Professional Summary</h2>
        {summary ? (
          <p className={styles.text}>{summary}</p>
        ) : (
          <p className={styles.empty}>No summary available.</p>
        )}
      </section>
    );
  }

  return (
    <EditableSection title="Professional Summary" onSave={handleSave}>
      {({ isEditing }) => (
        <div data-testid="summary-section">
          {isEditing ? (
            <div className={styles.formField}>
              <textarea
                value={formData}
                onChange={(e) => handleChange(e.target.value)}
                className={`${styles.textarea} ${validationError ? styles.textareaError : ''}`}
                rows={6}
                placeholder="Enter your professional summary..."
              />
              {validationError && (
                <span className={styles.errorText}>{validationError}</span>
              )}
            </div>
          ) : (
            <>
              {summary ? (
                <p className={styles.text}>{summary}</p>
              ) : (
                <p className={styles.empty}>No summary available.</p>
              )}
            </>
          )}
        </div>
      )}
    </EditableSection>
  );
}
