import { ReactNode, useState } from 'react';
import { Pencil, Check, X } from 'lucide-react';
import { StatusMessage } from './StatusMessage';
import styles from './EditableSection.module.css';

type EditState = 'viewing' | 'editing' | 'saving';

interface EditableSectionProps {
  children: (props: { isEditing: boolean }) => ReactNode;
  onSave: () => Promise<void>;
  title: string;
  placeholderContent?: ReactNode;
}

export function EditableSection({ children, onSave, title, placeholderContent }: EditableSectionProps) {
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
      {editState === 'viewing' && (
        <button
          onClick={handleEdit}
          className={styles.editIcon}
          aria-label={`Edit ${title}`}
        >
          <Pencil size={14} />
        </button>
      )}

      {(editState === 'editing' || editState === 'saving') && (
        <div className={styles.editActions}>
          {editState === 'editing' && (
            <>
              <button
                onClick={handleSave}
                className={`${styles.actionButton} ${styles.saveIcon}`}
                aria-label={`Save ${title}`}
              >
                <Check size={14} />
              </button>
              <button
                onClick={handleCancel}
                className={`${styles.actionButton} ${styles.cancelIcon}`}
                aria-label={`Cancel editing ${title}`}
              >
                <X size={14} />
              </button>
            </>
          )}
          {editState === 'saving' && (
            <span className={styles.saving}>Saving...</span>
          )}
        </div>
      )}

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

      {editState === 'viewing' && placeholderContent}
    </div>
  );
}
