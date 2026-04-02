import { describe, it, expect, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { InlineCreateForm } from '../../components/InlineCreateForm';

describe('InlineCreateForm', () => {
  it('renders with input and buttons', () => {
    render(
      <InlineCreateForm
        onConfirm={vi.fn()}
        onCancel={vi.fn()}
        placeholder="Enter name..."
        confirmLabel="Create"
      />
    );
    expect(screen.getByRole('textbox', { name: /name/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /create/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /cancel/i })).toBeInTheDocument();
  });

  it('auto-focuses the input on mount', () => {
    render(
      <InlineCreateForm onConfirm={vi.fn()} onCancel={vi.fn()} />
    );
    expect(screen.getByRole('textbox', { name: /name/i })).toHaveFocus();
  });

  it('shows error on empty submit', async () => {
    const user = userEvent.setup();
    render(
      <InlineCreateForm onConfirm={vi.fn()} onCancel={vi.fn()} />
    );
    await user.click(screen.getByRole('button', { name: /create/i }));
    expect(screen.getByText('Name cannot be empty')).toBeInTheDocument();
  });

  it('does not call onConfirm on empty submit', async () => {
    const user = userEvent.setup();
    const onConfirm = vi.fn();
    render(
      <InlineCreateForm onConfirm={onConfirm} onCancel={vi.fn()} />
    );
    await user.click(screen.getByRole('button', { name: /create/i }));
    expect(onConfirm).not.toHaveBeenCalled();
  });

  it('calls onConfirm with trimmed value on submit', async () => {
    const user = userEvent.setup();
    const onConfirm = vi.fn().mockResolvedValue(undefined);
    render(
      <InlineCreateForm onConfirm={onConfirm} onCancel={vi.fn()} />
    );
    await user.type(screen.getByRole('textbox', { name: /name/i }), '  My Resume  ');
    await user.click(screen.getByRole('button', { name: /create/i }));
    await waitFor(() => {
      expect(onConfirm).toHaveBeenCalledWith('My Resume');
    });
  });

  it('calls onCancel when Cancel button is clicked', async () => {
    const user = userEvent.setup();
    const onCancel = vi.fn();
    render(
      <InlineCreateForm onConfirm={vi.fn()} onCancel={onCancel} />
    );
    await user.click(screen.getByRole('button', { name: /cancel/i }));
    expect(onCancel).toHaveBeenCalled();
  });

  it('calls onCancel on Escape key', async () => {
    const user = userEvent.setup();
    const onCancel = vi.fn();
    render(
      <InlineCreateForm onConfirm={vi.fn()} onCancel={onCancel} />
    );
    await user.keyboard('{Escape}');
    expect(onCancel).toHaveBeenCalled();
  });

  it('disables buttons while submitting', async () => {
    const user = userEvent.setup();
    let resolveConfirm: () => void;
    const onConfirm = vi.fn().mockReturnValue(
      new Promise<void>((resolve) => { resolveConfirm = resolve; })
    );
    render(
      <InlineCreateForm onConfirm={onConfirm} onCancel={vi.fn()} />
    );
    await user.type(screen.getByRole('textbox', { name: /name/i }), 'Test');
    await user.click(screen.getByRole('button', { name: /create/i }));

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /creating/i })).toBeDisabled();
    });

    resolveConfirm!();
  });

  it('shows inline error when onConfirm throws', async () => {
    const user = userEvent.setup();
    const onConfirm = vi.fn().mockRejectedValue(new Error('Server error'));
    render(
      <InlineCreateForm onConfirm={onConfirm} onCancel={vi.fn()} />
    );
    await user.type(screen.getByRole('textbox', { name: /name/i }), 'Test');
    await user.click(screen.getByRole('button', { name: /create/i }));
    await waitFor(() => {
      expect(screen.getByText('Server error')).toBeInTheDocument();
    });
  });
});
