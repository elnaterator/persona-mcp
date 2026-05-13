import { useQuery } from '@tanstack/react-query';
import { getResume } from '../../services/api';
import ContactSection from './ContactSection';
import SummarySection from './SummarySection';
import ExperienceSection from './ExperienceSection';
import EducationSection from './EducationSection';
import SkillsSection from './SkillsSection';
import { LoadingSpinner } from '../../components/LoadingSpinner';
import styles from './ResumeView.module.css';

const ROOT_RESUME_KEY = ['resume', 'root'] as const;

export default function ResumeView() {
  const { data: resume, isPending, error, isError, refetch } = useQuery({
    queryKey: ROOT_RESUME_KEY,
    queryFn: getResume,
  });

  if (isPending) {
    return (
      <div className={styles.centerContainer}>
        <LoadingSpinner />
      </div>
    );
  }

  // Initial load failed (no data ever loaded) — full error screen with retry
  if (isError && !resume) {
    const message = error instanceof Error ? error.message : 'Failed to fetch resume data';
    return (
      <div className={styles.centerContainer}>
        <p className={styles.inlineError} role="alert">{message}</p>
        <button
          onClick={() => refetch()}
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
        <p className={styles.inlineError} role="alert">No resume data available</p>
      </div>
    );
  }

  const refreshErrorMsg =
    isError && resume
      ? error instanceof Error
        ? error.message
        : 'Failed to refresh resume data'
      : null;

  const handleUpdate = () => {
    refetch();
  };

  return (
    <div className={styles.container}>
      {refreshErrorMsg && (
        <p className={styles.inlineError} role="alert">{refreshErrorMsg}</p>
      )}
      <ContactSection contact={resume.contact} onUpdate={handleUpdate} />
      <SummarySection summary={resume.summary} onUpdate={handleUpdate} />
      <ExperienceSection experience={resume.experience} onUpdate={handleUpdate} />
      <EducationSection education={resume.education} onUpdate={handleUpdate} />
      <SkillsSection skills={resume.skills} onUpdate={handleUpdate} />
    </div>
  );
}
