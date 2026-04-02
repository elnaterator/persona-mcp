import { useEffect, useRef, useState } from 'react';
import styles from './InlineCreateForm.module.css';

interface InlineCreateFormProps {
  onConfirm: (label: string) => Promise<void>;
  onCancel: () => void;
  placeholder?: string;
  confirmLabel?: string;
}

export function InlineCreateForm({
  onConfirm,
  onCancel,
  placeholder = 'Enter name...',
  confirmLabel = 'Create',
}: InlineCreateFormProps) {
  const [value, setValue] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        onCancel();
      }
    };
    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [onCancel]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!value.trim()) {
      setError('Name cannot be empty');
      return;
    }
    setError(null);
    setSubmitting(true);
    try {
      await onConfirm(value.trim());
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create');
      setSubmitting(false);
    }
  };

  return (
    <form className={styles.form} onSubmit={handleSubmit} data-testid="inline-create-form">
      <input
        ref={inputRef}
        type="text"
        value={value}
        onChange={(e) => {
          setValue(e.target.value);
          if (error) setError(null);
        }}
        placeholder={placeholder}
        className={`${styles.input}${error ? ` ${styles.inputError}` : ''}`}
        disabled={submitting}
        aria-label="Name"
      />
      <div className={styles.buttons}>
        <button
          type="submit"
          className={styles.confirmBtn}
          disabled={submitting}
        >
          {submitting ? 'Creating...' : confirmLabel}
        </button>
        <button
          type="button"
          className={styles.cancelBtn}
          onClick={onCancel}
          disabled={submitting}
        >
          Cancel
        </button>
      </div>
      {error && <p className={styles.error}>{error}</p>}
    </form>
  );
}
