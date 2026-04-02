import { useEffect, useState } from 'react';
import type { ContactInfo } from '../types/resume';
import { EditableSection } from './EditableSection';
import { updateContact, updateVersionContact } from '../services/api';
import styles from './ContactSection.module.css';

interface ContactSectionProps {
  contact: ContactInfo;
  onUpdate?: () => void;
  versionId?: number;
}

function ContactReadView({ contact }: { contact: ContactInfo }) {
  const details: string[] = [];
  if (contact.email) details.push(contact.email);
  if (contact.phone) details.push(contact.phone);
  if (contact.location) details.push(contact.location);

  const links: { label: string; href: string }[] = [];
  if (contact.linkedin) links.push({ label: 'LinkedIn', href: contact.linkedin });
  if (contact.website) links.push({ label: 'Website', href: contact.website });
  if (contact.github) links.push({ label: 'GitHub', href: contact.github });

  return (
    <div className={styles.readView}>
      {contact.name && <h1 className={styles.nameHeading}>{contact.name}</h1>}
      {(details.length > 0 || links.length > 0) && (
        <div className={styles.contactRow}>
          {details.map((d, i) => (
            <span key={i} className={styles.contactItem}>{d}</span>
          ))}
          {links.map((l, i) => (
            <a
              key={i}
              href={l.href}
              target="_blank"
              rel="noopener noreferrer"
              className={`${styles.contactItem} ${styles.contactLink}`}
            >
              {l.label}
            </a>
          ))}
        </div>
      )}
    </div>
  );
}

export default function ContactSection({ contact, onUpdate, versionId }: ContactSectionProps) {
  const [formData, setFormData] = useState<ContactInfo>(contact);
  const [validationErrors, setValidationErrors] = useState<Record<string, string>>({});

  useEffect(() => {
    setFormData(contact);
    setValidationErrors({});
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
    if (versionId !== undefined) {
      await updateVersionContact(versionId, formData);
    } else {
      await updateContact(formData);
    }
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
      <section data-testid="contact-section">
        <ContactReadView contact={contact} />
      </section>
    );
  }

  return (
    <EditableSection title="Contact Information" onSave={handleSave}>
      {({ isEditing }) => (
        <div data-testid="contact-section">
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
            <ContactReadView contact={contact} />
          )}
        </div>
      )}
    </EditableSection>
  );
}
