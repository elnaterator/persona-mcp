import { useState, useEffect } from 'react';
import { getResume } from '../services/api';
import type { Resume } from '../types/resume';
import ContactSection from './ContactSection';
import SummarySection from './SummarySection';
import ExperienceSection from './ExperienceSection';
import EducationSection from './EducationSection';
import SkillsSection from './SkillsSection';
import { LoadingSpinner } from './LoadingSpinner';
import { StatusMessage } from './StatusMessage';
import styles from './ResumeView.module.css';

export default function ResumeView() {
  const [resume, setResume] = useState<Resume | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [refreshError, setRefreshError] = useState<string | null>(null);

  useEffect(() => {
    loadResume();
  }, []);

  const loadResume = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await getResume();
      setResume(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch resume data');
    } finally {
      setLoading(false);
    }
  };

  const handleUpdate = async () => {
    try {
      setRefreshError(null);
      const data = await getResume();
      setResume(data);
    } catch (err) {
      // On refresh failure, keep existing data visible but show error
      setRefreshError(err instanceof Error ? err.message : 'Failed to refresh resume data');
    }
  };

  if (loading) {
    return (
      <div className={styles.centerContainer}>
        <LoadingSpinner />
      </div>
    );
  }

  if (error) {
    return (
      <div className={styles.centerContainer}>
        <StatusMessage type="error" message={error} />
        <button
          onClick={loadResume}
          className={styles.retryButton}
          aria-label="Retry loading resume"
        >
          Retry
        </button>
      </div>
    );
  }

  if (!resume) {
    return (
      <div className={styles.centerContainer}>
        <StatusMessage type="error" message="No resume data available" />
      </div>
    );
  }

  return (
    <div className={styles.container}>
      {refreshError && (
        <div className={styles.refreshError}>
          <StatusMessage
            type="error"
            message={refreshError}
            onDismiss={() => setRefreshError(null)}
          />
        </div>
      )}
      <ContactSection contact={resume.contact} onUpdate={handleUpdate} />
      <SummarySection summary={resume.summary} onUpdate={handleUpdate} />
      <ExperienceSection experience={resume.experience} onUpdate={handleUpdate} />
      <EducationSection education={resume.education} onUpdate={handleUpdate} />
      <SkillsSection skills={resume.skills} onUpdate={handleUpdate} />
    </div>
  );
}
