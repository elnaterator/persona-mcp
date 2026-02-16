import { useEffect, useState } from 'react';
import type { ContactInfo } from '../types/resume';
import { EditableSection } from './EditableSection';
import { updateContact } from '../services/api';
import styles from './ContactSection.module.css';

interface ContactSectionProps {
  contact: ContactInfo;
  onUpdate?: () => void;
}

export default function ContactSection({ contact, onUpdate }: ContactSectionProps) {
  const [formData, setFormData] = useState<ContactInfo>(contact);
  const [validationErrors, setValidationErrors] = useState<Record<string, string>>({});

  useEffect(() => {
    setFormData(contact);
  }, [contact]);

  const validateEmail = (email: string): boolean => {
    if (!email) return true;
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
  };

  const handleSave = async () => {
    const errors: Record<string, string> = {};

    if (formData.email && !validateEmail(formData.email)) {
      errors.email = 'Invalid email format';
    }

    if (Object.keys(errors).length > 0) {
      setValidationErrors(errors);
      throw new Error('Please fix validation errors');
    }

    setValidationErrors({});
    await updateContact(formData);
    if (onUpdate) {
      onUpdate();
    }
  };

  const handleFieldChange = (field: keyof ContactInfo, value: string) => {
    setFormData((prev) => ({
      ...prev,
      [field]: value || null,
    }));
    if (validationErrors[field]) {
      setValidationErrors((prev) => {
        const updated = { ...prev };
        delete updated[field];
        return updated;
      });
    }
  };

  if (!onUpdate) {
    return (
      <section className={styles.container} data-testid="contact-section">
        <h2 className={styles.heading}>Contact Information</h2>
        <div className={styles.content}>
          {contact.name && (
            <div className={styles.field}>
              <span className={styles.label}>Name:</span>
              <span className={styles.value}>{contact.name}</span>
            </div>
          )}
          {contact.email && (
            <div className={styles.field}>
              <span className={styles.label}>Email:</span>
              <span className={styles.value}>{contact.email}</span>
            </div>
          )}
          {contact.phone && (
            <div className={styles.field}>
              <span className={styles.label}>Phone:</span>
              <span className={styles.value}>{contact.phone}</span>
            </div>
          )}
          {contact.location && (
            <div className={styles.field}>
              <span className={styles.label}>Location:</span>
              <span className={styles.value}>{contact.location}</span>
            </div>
          )}
          {(contact.linkedin || contact.website || contact.github) && (
            <div className={styles.links}>
              {contact.linkedin && (
                <a
                  href={contact.linkedin}
                  target="_blank"
                  rel="noopener noreferrer"
                  className={styles.link}
                >
                  LinkedIn
                </a>
              )}
              {contact.website && (
                <a
                  href={contact.website}
                  target="_blank"
                  rel="noopener noreferrer"
                  className={styles.link}
                >
                  Website
                </a>
              )}
              {contact.github && (
                <a
                  href={contact.github}
                  target="_blank"
                  rel="noopener noreferrer"
                  className={styles.link}
                >
                  GitHub
                </a>
              )}
            </div>
          )}
        </div>
      </section>
    );
  }

  return (
    <EditableSection title="Contact Information" onSave={handleSave}>
      {({ isEditing }) => (
        <div className={styles.content} data-testid="contact-section">
          {isEditing ? (
            <form className={styles.form} onSubmit={(e) => e.preventDefault()}>
              <div className={styles.formField}>
                <label htmlFor="name" className={styles.formLabel}>
                  Name
                </label>
                <input
                  type="text"
                  id="name"
                  value={formData.name || ''}
                  onChange={(e) => handleFieldChange('name', e.target.value)}
                  className={styles.input}
                />
              </div>

              <div className={styles.formField}>
                <label htmlFor="email" className={styles.formLabel}>
                  Email
                </label>
                <input
                  type="email"
                  id="email"
                  value={formData.email || ''}
                  onChange={(e) => handleFieldChange('email', e.target.value)}
                  className={`${styles.input} ${validationErrors.email ? styles.inputError : ''}`}
                />
                {validationErrors.email && (
                  <span className={styles.errorText}>{validationErrors.email}</span>
                )}
              </div>

              <div className={styles.formField}>
                <label htmlFor="phone" className={styles.formLabel}>
                  Phone
                </label>
                <input
                  type="tel"
                  id="phone"
                  value={formData.phone || ''}
                  onChange={(e) => handleFieldChange('phone', e.target.value)}
                  className={styles.input}
                />
              </div>

              <div className={styles.formField}>
                <label htmlFor="location" className={styles.formLabel}>
                  Location
                </label>
                <input
                  type="text"
                  id="location"
                  value={formData.location || ''}
                  onChange={(e) => handleFieldChange('location', e.target.value)}
                  className={styles.input}
                />
              </div>

              <div className={styles.formField}>
                <label htmlFor="linkedin" className={styles.formLabel}>
                  LinkedIn
                </label>
                <input
                  type="url"
                  id="linkedin"
                  value={formData.linkedin || ''}
                  onChange={(e) => handleFieldChange('linkedin', e.target.value)}
                  className={styles.input}
                  placeholder="https://linkedin.com/in/username"
                />
              </div>

              <div className={styles.formField}>
                <label htmlFor="website" className={styles.formLabel}>
                  Website
                </label>
                <input
                  type="url"
                  id="website"
                  value={formData.website || ''}
                  onChange={(e) => handleFieldChange('website', e.target.value)}
                  className={styles.input}
                  placeholder="https://example.com"
                />
              </div>

              <div className={styles.formField}>
                <label htmlFor="github" className={styles.formLabel}>
                  GitHub
                </label>
                <input
                  type="url"
                  id="github"
                  value={formData.github || ''}
                  onChange={(e) => handleFieldChange('github', e.target.value)}
                  className={styles.input}
                  placeholder="https://github.com/username"
                />
              </div>
            </form>
          ) : (
            <>
              {contact.name && (
                <div className={styles.field}>
                  <span className={styles.label}>Name:</span>
                  <span className={styles.value}>{contact.name}</span>
                </div>
              )}
              {contact.email && (
                <div className={styles.field}>
                  <span className={styles.label}>Email:</span>
                  <span className={styles.value}>{contact.email}</span>
                </div>
              )}
              {contact.phone && (
                <div className={styles.field}>
                  <span className={styles.label}>Phone:</span>
                  <span className={styles.value}>{contact.phone}</span>
                </div>
              )}
              {contact.location && (
                <div className={styles.field}>
                  <span className={styles.label}>Location:</span>
                  <span className={styles.value}>{contact.location}</span>
                </div>
              )}
              {(contact.linkedin || contact.website || contact.github) && (
                <div className={styles.links}>
                  {contact.linkedin && (
                    <a
                      href={contact.linkedin}
                      target="_blank"
                      rel="noopener noreferrer"
                      className={styles.link}
                    >
                      LinkedIn
                    </a>
                  )}
                  {contact.website && (
                    <a
                      href={contact.website}
                      target="_blank"
                      rel="noopener noreferrer"
                      className={styles.link}
                    >
                      Website
                    </a>
                  )}
                  {contact.github && (
                    <a
                      href={contact.github}
                      target="_blank"
                      rel="noopener noreferrer"
                      className={styles.link}
                    >
                      GitHub
                    </a>
                  )}
                </div>
              )}
            </>
          )}
        </div>
      )}
    </EditableSection>
  );
}
