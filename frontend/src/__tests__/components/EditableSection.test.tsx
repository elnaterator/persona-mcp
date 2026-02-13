import { describe, it, expect, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { useState } from 'react';
import { EditableSection } from '../../components/EditableSection';

describe('EditableSection', () => {
  it('preserves form data and stays in edit mode on save failure', async () => {
    const user = userEvent.setup();
    const mockOnSave = vi.fn().mockRejectedValue(new Error('Save failed'));

    // Wrapper component that maintains state like real sections do
    function TestComponent() {
      const [value, setValue] = useState('');

      return (
        <EditableSection title="Test Section" onSave={mockOnSave}>
          {({ isEditing }) =>
            isEditing ? (
              <input
                type="text"
                value={value}
                onChange={(e) => setValue(e.target.value)}
                data-testid="test-input"
              />
            ) : (
              <div data-testid="view-mode">View Mode: {value}</div>
            )
          }
        </EditableSection>
      );
    }

    render(<TestComponent />);

    // Click edit button
    const editButton = screen.getByRole('button', { name: /edit test section/i });
    await user.click(editButton);

    // Verify we're in edit mode
    expect(screen.getByTestId('test-input')).toBeInTheDocument();

    // Enter some data
    const input = screen.getByTestId('test-input');
    await user.type(input, 'Important data');

    // Click save button
    const saveButton = screen.getByRole('button', { name: /save test section/i });
    await user.click(saveButton);

    // Wait for error message
    await waitFor(() => {
      expect(screen.getByText(/save failed/i)).toBeInTheDocument();
    });

    // Verify we're still in edit mode (not viewing)
    expect(screen.queryByTestId('view-mode')).not.toBeInTheDocument();
    expect(screen.getByTestId('test-input')).toBeInTheDocument();

    // Verify the form input is still present with data (data preserved)
    expect(screen.getByTestId('test-input')).toHaveValue('Important data');
  });

  it('allows retry after save failure', async () => {
    const user = userEvent.setup();
    const mockOnSave = vi
      .fn()
      .mockRejectedValueOnce(new Error('First attempt failed'))
      .mockResolvedValueOnce(undefined);

    render(
      <EditableSection title="Test Section" onSave={mockOnSave}>
        {({ isEditing }) => (isEditing ? <div>Edit Mode</div> : <div>View Mode</div>)}
      </EditableSection>
    );

    // Enter edit mode
    const editButton = screen.getByRole('button', { name: /edit test section/i });
    await user.click(editButton);

    // First save attempt fails
    const saveButton = screen.getByRole('button', { name: /save test section/i });
    await user.click(saveButton);

    await waitFor(() => {
      expect(screen.getByText(/first attempt failed/i)).toBeInTheDocument();
    });

    // Still in edit mode
    expect(screen.getByText('Edit Mode')).toBeInTheDocument();

    // Retry save (second attempt succeeds)
    const retrySaveButton = screen.getByRole('button', { name: /save test section/i });
    await user.click(retrySaveButton);

    // Wait for success
    await waitFor(() => {
      expect(screen.getByText(/changes saved successfully/i)).toBeInTheDocument();
    });

    // Should transition to view mode
    await waitFor(() => {
      expect(screen.getByText('View Mode')).toBeInTheDocument();
    });
  });
});
