import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import ResumeView from '../../components/ResumeView';
import * as api from '../../services/api';
import type { Resume } from '../../types/resume';

// Mock the API module
vi.mock('../../services/api');

const mockResume: Resume = {
  contact: {
    name: 'John Doe',
    email: 'john@example.com',
    phone: '555-1234',
    location: 'San Francisco, CA',
    linkedin: 'https://linkedin.com/in/johndoe',
    website: 'https://johndoe.com',
    github: 'https://github.com/johndoe',
  },
  summary: 'Experienced software engineer with a passion for building great products.',
  experience: [
    {
      title: 'Senior Engineer',
      company: 'Tech Corp',
      start_date: '2020-01',
      end_date: '2024-01',
      location: 'San Francisco, CA',
      highlights: ['Built awesome features', 'Led team of 5'],
    },
  ],
  education: [
    {
      institution: 'University of Example',
      degree: 'BS Computer Science',
      field: 'Computer Science',
      start_date: '2012-09',
      end_date: '2016-05',
      honors: 'Cum Laude',
    },
  ],
  skills: [
    { name: 'JavaScript', category: 'Languages' },
    { name: 'React', category: 'Frameworks' },
  ],
};

describe('ResumeView', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('shows loading spinner during fetch', () => {
    // Mock API to never resolve (simulate loading state)
    vi.mocked(api.getResume).mockReturnValue(new Promise(() => {}));

    render(<ResumeView />);

    expect(screen.getByTestId('loading-spinner')).toBeInTheDocument();
  });

  it('renders all five sections when data is present', async () => {
    vi.mocked(api.getResume).mockResolvedValue(mockResume);

    render(<ResumeView />);

    // Wait for data to load
    await waitFor(() => {
      expect(screen.queryByTestId('loading-spinner')).not.toBeInTheDocument();
    });

    // Verify all sections are rendered
    expect(screen.getByTestId('contact-section')).toBeInTheDocument();
    expect(screen.getByTestId('summary-section')).toBeInTheDocument();
    expect(screen.getByTestId('experience-section')).toBeInTheDocument();
    expect(screen.getByTestId('education-section')).toBeInTheDocument();
    expect(screen.getByTestId('skills-section')).toBeInTheDocument();
  });

  it('shows error message on fetch failure', async () => {
    const errorMessage = 'Failed to fetch resume data';
    vi.mocked(api.getResume).mockRejectedValue(new Error(errorMessage));

    render(<ResumeView />);

    // Wait for error to appear
    await waitFor(() => {
      expect(screen.getByText(/failed to fetch/i)).toBeInTheDocument();
    });

    expect(screen.queryByTestId('contact-section')).not.toBeInTheDocument();
  });

  it('displays resume data in sections', async () => {
    vi.mocked(api.getResume).mockResolvedValue(mockResume);

    render(<ResumeView />);

    await waitFor(() => {
      expect(screen.queryByTestId('loading-spinner')).not.toBeInTheDocument();
    });

    // Check that data is passed to sections
    expect(screen.getByText('John Doe')).toBeInTheDocument();
    expect(screen.getByText('john@example.com')).toBeInTheDocument();
    expect(screen.getByText(/experienced software engineer/i)).toBeInTheDocument();
    expect(screen.getByText('Senior Engineer')).toBeInTheDocument();
    expect(screen.getByText('University of Example')).toBeInTheDocument();
    expect(screen.getByText('JavaScript')).toBeInTheDocument();
  });

  // T046: Error scenario tests for US4 (Responsive Error Handling)
  describe('Error Handling', () => {
    it('shows error with retry button when server is unavailable', async () => {
      const errorMessage = 'Network error: Failed to fetch';
      vi.mocked(api.getResume).mockRejectedValue(new Error(errorMessage));

      render(<ResumeView />);

      // Wait for error to appear
      await waitFor(() => {
        expect(screen.getByText(/network error/i)).toBeInTheDocument();
      });

      // Verify retry button is present
      const retryButton = screen.getByRole('button', { name: /retry/i });
      expect(retryButton).toBeInTheDocument();
    });

    it('retries fetching resume when retry button is clicked', async () => {
      const user = userEvent.setup();

      // First call fails
      vi.mocked(api.getResume).mockRejectedValueOnce(new Error('Network error'));

      render(<ResumeView />);

      // Wait for error and retry button
      await waitFor(() => {
        expect(screen.getByRole('button', { name: /retry/i })).toBeInTheDocument();
      });

      // Second call succeeds
      vi.mocked(api.getResume).mockResolvedValueOnce(mockResume);

      // Click retry button
      const retryButton = screen.getByRole('button', { name: /retry/i });
      await user.click(retryButton);

      // Verify data loads successfully
      await waitFor(() => {
        expect(screen.getByText('John Doe')).toBeInTheDocument();
      });

      expect(screen.queryByRole('button', { name: /retry/i })).not.toBeInTheDocument();
    });

    it('shows refresh error without hiding existing data', async () => {
      const user = userEvent.setup();

      // Initial load succeeds
      vi.mocked(api.getResume).mockResolvedValueOnce(mockResume);

      render(<ResumeView />);

      // Wait for data to load
      await waitFor(() => {
        expect(screen.getByText('John Doe')).toBeInTheDocument();
      });

      // All sections are visible
      expect(screen.getByTestId('contact-section')).toBeInTheDocument();
      expect(screen.getByTestId('summary-section')).toBeInTheDocument();
      expect(screen.getByTestId('experience-section')).toBeInTheDocument();
      expect(screen.getByTestId('education-section')).toBeInTheDocument();
      expect(screen.getByTestId('skills-section')).toBeInTheDocument();

      // Simulate a refresh failure (e.g., after edit)
      vi.mocked(api.getResume).mockRejectedValueOnce(new Error('Refresh failed'));

      // Trigger a section update (edit contact and save)
      const editButtons = screen.getAllByRole('button', { name: /edit/i });
      await user.click(editButtons[0]); // Click first edit button (contact section)

      // Find and click save button
      const saveButton = screen.getByRole('button', { name: /save contact/i });
      await user.click(saveButton);

      // Wait for refresh error to appear
      await waitFor(() => {
        expect(screen.getByText(/refresh failed/i)).toBeInTheDocument();
      });

      // Verify all sections are STILL visible despite the error
      expect(screen.getByText('John Doe')).toBeInTheDocument();
      expect(screen.getByTestId('contact-section')).toBeInTheDocument();
      expect(screen.getByTestId('summary-section')).toBeInTheDocument();
      expect(screen.getByTestId('experience-section')).toBeInTheDocument();
      expect(screen.getByTestId('education-section')).toBeInTheDocument();
      expect(screen.getByTestId('skills-section')).toBeInTheDocument();
    });
  });
});
