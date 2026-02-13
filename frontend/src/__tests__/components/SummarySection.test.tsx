import { describe, it, expect, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import SummarySection from '../../components/SummarySection';
import * as api from '../../services/api';

const testSummary = 'Experienced software engineer with a passion for building scalable applications.';

describe('SummarySection (view mode)', () => {
  it('renders summary text when present', () => {
    render(<SummarySection summary={testSummary} />);
    expect(screen.getByText(testSummary)).toBeInTheDocument();
  });

  it('shows empty state when summary is empty', () => {
    render(<SummarySection summary="" />);
    expect(screen.getByText(/no summary available/i)).toBeInTheDocument();
  });
});

describe('SummarySection (edit mode)', () => {
  it('toggles to edit mode when edit button is clicked', async () => {
    const user = userEvent.setup();
    render(<SummarySection summary={testSummary} onUpdate={() => {}} />);

    const editButton = screen.getByRole('button', { name: /edit/i });
    await user.click(editButton);

    // Textarea should be visible
    const textarea = screen.getByRole('textbox');
    expect(textarea).toBeInTheDocument();
    expect(textarea).toHaveValue(testSummary);
  });

  it('pre-fills textarea with current summary', async () => {
    const user = userEvent.setup();
    render(<SummarySection summary={testSummary} onUpdate={() => {}} />);

    await user.click(screen.getByRole('button', { name: /edit/i }));

    const textarea = screen.getByRole('textbox');
    expect(textarea).toHaveValue(testSummary);
  });

  it('calls updateSummary API on save and shows success', async () => {
    const user = userEvent.setup();
    const updateSpy = vi.spyOn(api, 'updateSummary').mockResolvedValue({ message: 'Success' });
    const onUpdate = vi.fn();

    render(<SummarySection summary={testSummary} onUpdate={onUpdate} />);

    await user.click(screen.getByRole('button', { name: /edit/i }));

    const textarea = screen.getByRole('textbox');
    await user.clear(textarea);
    await user.type(textarea, 'Updated summary text.');

    await user.click(screen.getByRole('button', { name: /save/i }));

    await waitFor(() => {
      expect(updateSpy).toHaveBeenCalledWith('Updated summary text.');
    });

    await waitFor(() => {
      expect(onUpdate).toHaveBeenCalled();
    });

    updateSpy.mockRestore();
  });

  it('reverts to view mode on cancel without saving', async () => {
    const user = userEvent.setup();
    const updateSpy = vi.spyOn(api, 'updateSummary');

    render(<SummarySection summary={testSummary} onUpdate={() => {}} />);

    await user.click(screen.getByRole('button', { name: /edit/i }));

    const textarea = screen.getByRole('textbox');
    await user.clear(textarea);
    await user.type(textarea, 'Changed text');

    await user.click(screen.getByRole('button', { name: /cancel/i }));

    // Should be back in view mode with original text
    expect(screen.getByText(testSummary)).toBeInTheDocument();
    expect(screen.queryByRole('textbox')).not.toBeInTheDocument();
    expect(updateSpy).not.toHaveBeenCalled();

    updateSpy.mockRestore();
  });

  it('shows validation error when summary text is empty', async () => {
    const user = userEvent.setup();
    render(<SummarySection summary={testSummary} onUpdate={() => {}} />);

    await user.click(screen.getByRole('button', { name: /edit/i }));

    const textarea = screen.getByRole('textbox');
    await user.clear(textarea);

    await user.click(screen.getByRole('button', { name: /save/i }));

    await waitFor(() => {
      const errors = screen.getAllByText(/summary cannot be empty/i);
      expect(errors.length).toBeGreaterThan(0);
    });
  });

  it('shows error message when API call fails', async () => {
    const user = userEvent.setup();
    const updateSpy = vi.spyOn(api, 'updateSummary').mockRejectedValue(
      new api.ApiClientError('Server error', 500, 'Internal server error')
    );

    render(<SummarySection summary={testSummary} onUpdate={() => {}} />);

    await user.click(screen.getByRole('button', { name: /edit/i }));
    await user.click(screen.getByRole('button', { name: /save/i }));

    await waitFor(() => {
      expect(screen.getByText(/server error/i)).toBeInTheDocument();
    });

    updateSpy.mockRestore();
  });
});
