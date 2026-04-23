import { useState } from 'react';
import { EditableSection } from './EditableSection';
import { updateSummary, updateVersionSummary } from '../services/api';
import { MarkdownContent } from './MarkdownContent';
import { AutoResizeTextarea } from './AutoResizeTextarea';
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
        <h2 className={styles.sectionLabel}>Summary</h2>
        {summary ? (
          <MarkdownContent>{summary}</MarkdownContent>
        ) : (
          <p className={styles.empty}>No summary available.</p>
        )}
      </section>
    );
  }

  const placeholder = !summary ? (
    <p className={styles.placeholder}>Click the pencil icon to add a summary</p>
  ) : undefined;

  return (
    <EditableSection title="Summary" onSave={handleSave} placeholderContent={placeholder}>
      {({ isEditing }) => (
        <div data-testid="summary-section">
          <h2 className={styles.sectionLabel}>Summary</h2>
          {isEditing ? (
            <div className={styles.formField}>
              <AutoResizeTextarea
                value={formData}
                onChange={handleChange}
                className={`${styles.textarea} ${validationError ? styles.textareaError : ''}`}
                placeholder="Enter your professional summary..."
              />
              {validationError && (
                <span className={styles.errorText}>{validationError}</span>
              )}
            </div>
          ) : (
            <>
              {summary && (
                <MarkdownContent>{summary}</MarkdownContent>
              )}
            </>
          )}
        </div>
      )}
    </EditableSection>
  );
}
