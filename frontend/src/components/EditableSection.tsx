import { ReactNode, useRef, useState } from 'react';
import { Pencil } from 'lucide-react';
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
  const [hovering, setHovering] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const touchTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const handleEdit = () => {
    setEditState('editing');
    setError(null);
    setSuccess(null);
    setHovering(false);
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

  const handleMouseEnter = () => setHovering(true);
  const handleMouseLeave = () => setHovering(false);

  const handleTouchStart = () => {
    setHovering(true);
    if (touchTimeoutRef.current) clearTimeout(touchTimeoutRef.current);
    touchTimeoutRef.current = setTimeout(() => setHovering(false), 3000);
  };

  return (
    <div
      className={styles.container}
      onMouseEnter={handleMouseEnter}
      onMouseLeave={handleMouseLeave}
      onTouchStart={handleTouchStart}
    >
      {editState === 'viewing' && (
        <button
          onClick={handleEdit}
          className={`${styles.editIcon}${hovering ? ` ${styles.editIconVisible}` : ''}`}
          aria-label={`Edit ${title}`}
        >
          <Pencil size={14} />
        </button>
      )}

      {(editState === 'editing' || editState === 'saving') && (
        <div className={styles.header}>
          <h2 className={styles.title}>{title}</h2>
          <div className={styles.actions}>
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
