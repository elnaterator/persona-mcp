import { ReactNode, useState } from 'react';
import { StatusMessage } from './StatusMessage';
import styles from './EditableSection.module.css';

type EditState = 'viewing' | 'editing' | 'saving';

interface EditableSectionProps {
  children: (props: { isEditing: boolean }) => ReactNode;
  onSave: () => Promise<void>;
  title: string;
}

export function EditableSection({ children, onSave, title }: EditableSectionProps) {
  const [editState, setEditState] = useState<EditState>('viewing');
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const handleEdit = () => {
    setEditState('editing');
    setError(null);
    setSuccess(null);
  };

  const handleCancel = () => {
    setEditState('viewing');
    setError(null);
    setSuccess(null);
  };

  const handleSave = async () => {
    setEditState('saving');
    setError(null);
    setSuccess(null);

    try {
      await onSave();
      setSuccess('Changes saved successfully');
      setEditState('viewing');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save changes');
      setEditState('editing');
    }
  };

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <h2 className={styles.title}>{title}</h2>
        <div className={styles.actions}>
          {editState === 'viewing' && (
            <button
              onClick={handleEdit}
              className={styles.button}
              aria-label={`Edit ${title}`}
            >
              Edit
            </button>
          )}
          {editState === 'editing' && (
            <>
              <button
                onClick={handleSave}
                className={`${styles.button} ${styles.primary}`}
                aria-label={`Save ${title}`}
              >
                Save
              </button>
              <button
                onClick={handleCancel}
                className={styles.button}
                aria-label={`Cancel editing ${title}`}
              >
                Cancel
              </button>
            </>
          )}
          {editState === 'saving' && (
            <span className={styles.saving}>Saving...</span>
          )}
        </div>
      </div>

      {error && (
        <StatusMessage
          type="error"
          message={error}
          onDismiss={() => setError(null)}
        />
      )}

      {success && (
        <StatusMessage
          type="success"
          message={success}
          onDismiss={() => setSuccess(null)}
        />
      )}

      <div className={styles.content}>
        {children({ isEditing: editState === 'editing' })}
      </div>
    </div>
  );
}
