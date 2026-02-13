import { describe, it, expect, vi } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { EntryForm } from '../../components/EntryForm'

describe('EntryForm', () => {
  const mockOnSubmit = vi.fn()
  const mockOnCancel = vi.fn()

  const simpleFieldConfig = [
    { name: 'title', label: 'Title', type: 'text' as const, required: true },
    { name: 'company', label: 'Company', type: 'text' as const, required: true },
    { name: 'location', label: 'Location', type: 'text' as const, required: false },
  ]

  const textareaFieldConfig = [
    { name: 'summary', label: 'Summary', type: 'textarea' as const, required: true },
  ]

  const highlightsFieldConfig = [
    { name: 'title', label: 'Title', type: 'text' as const, required: true },
    { name: 'highlights', label: 'Highlights', type: 'highlights' as const, required: false },
  ]

  beforeEach(() => {
    mockOnSubmit.mockClear()
    mockOnCancel.mockClear()
  })

  it('renders all fields from configuration', () => {
    render(
      <EntryForm
        fields={simpleFieldConfig}
        onSubmit={mockOnSubmit}
        onCancel={mockOnCancel}
      />
    )

    expect(screen.getByLabelText(/title/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/company/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/location/i)).toBeInTheDocument()
  })

  it('marks required fields with asterisk', () => {
    render(
      <EntryForm
        fields={simpleFieldConfig}
        onSubmit={mockOnSubmit}
        onCancel={mockOnCancel}
      />
    )

    const titleLabel = screen.getByText(/title/i)
    const companyLabel = screen.getByText(/company/i)
    const locationLabel = screen.getByText(/location/i)

    expect(titleLabel.textContent).toContain('*')
    expect(companyLabel.textContent).toContain('*')
    expect(locationLabel.textContent).not.toContain('*')
  })

  it('pre-fills form with initial data', () => {
    const initialData = {
      title: 'Software Engineer',
      company: 'Tech Corp',
      location: 'San Francisco',
    }

    render(
      <EntryForm
        fields={simpleFieldConfig}
        initialData={initialData}
        onSubmit={mockOnSubmit}
        onCancel={mockOnCancel}
      />
    )

    expect(screen.getByLabelText(/title/i)).toHaveValue('Software Engineer')
    expect(screen.getByLabelText(/company/i)).toHaveValue('Tech Corp')
    expect(screen.getByLabelText(/location/i)).toHaveValue('San Francisco')
  })

  it('validates required fields on submit', async () => {
    const user = userEvent.setup()

    render(
      <EntryForm
        fields={simpleFieldConfig}
        onSubmit={mockOnSubmit}
        onCancel={mockOnCancel}
      />
    )

    const submitButton = screen.getByRole('button', { name: /save/i })
    await user.click(submitButton)

    await waitFor(() => {
      expect(screen.getByText(/title is required/i)).toBeInTheDocument()
      expect(screen.getByText(/company is required/i)).toBeInTheDocument()
    })

    expect(mockOnSubmit).not.toHaveBeenCalled()
  })

  it('submits valid data with correct shape', async () => {
    const user = userEvent.setup()

    render(
      <EntryForm
        fields={simpleFieldConfig}
        onSubmit={mockOnSubmit}
        onCancel={mockOnCancel}
      />
    )

    await user.type(screen.getByLabelText(/title/i), 'Senior Engineer')
    await user.type(screen.getByLabelText(/company/i), 'Big Tech')
    await user.type(screen.getByLabelText(/location/i), 'New York')

    await user.click(screen.getByRole('button', { name: /save/i }))

    await waitFor(() => {
      expect(mockOnSubmit).toHaveBeenCalledWith({
        title: 'Senior Engineer',
        company: 'Big Tech',
        location: 'New York',
      })
    })
  })

  it('calls onCancel when cancel button clicked', async () => {
    const user = userEvent.setup()

    render(
      <EntryForm
        fields={simpleFieldConfig}
        onSubmit={mockOnSubmit}
        onCancel={mockOnCancel}
      />
    )

    await user.click(screen.getByRole('button', { name: /cancel/i }))

    expect(mockOnCancel).toHaveBeenCalled()
    expect(mockOnSubmit).not.toHaveBeenCalled()
  })

  it('renders textarea for textarea type fields', () => {
    render(
      <EntryForm
        fields={textareaFieldConfig}
        onSubmit={mockOnSubmit}
        onCancel={mockOnCancel}
      />
    )

    const summaryInput = screen.getByLabelText(/summary/i)
    expect(summaryInput.tagName).toBe('TEXTAREA')
  })

  it('handles highlights field as dynamic list', async () => {
    const user = userEvent.setup()

    render(
      <EntryForm
        fields={highlightsFieldConfig}
        onSubmit={mockOnSubmit}
        onCancel={mockOnCancel}
      />
    )

    expect(screen.getByText(/highlights/i)).toBeInTheDocument()

    const addButton = screen.getByRole('button', { name: /add highlight/i })
    await user.click(addButton)

    const highlightInputs = screen.getAllByPlaceholderText(/highlight/i)
    expect(highlightInputs).toHaveLength(1)

    await user.type(highlightInputs[0], 'Led team of 5 engineers')

    await user.click(addButton)
    const updatedInputs = screen.getAllByPlaceholderText(/highlight/i)
    expect(updatedInputs).toHaveLength(2)
  })

  it('removes highlight from list when remove button clicked', async () => {
    const user = userEvent.setup()

    render(
      <EntryForm
        fields={highlightsFieldConfig}
        onSubmit={mockOnSubmit}
        onCancel={mockOnCancel}
      />
    )

    const addButton = screen.getByRole('button', { name: /add highlight/i })
    await user.click(addButton)
    await user.click(addButton)

    let highlightInputs = screen.getAllByPlaceholderText(/highlight/i)
    expect(highlightInputs).toHaveLength(2)

    const removeButtons = screen.getAllByRole('button', { name: /remove/i })
    await user.click(removeButtons[0])

    highlightInputs = screen.getAllByPlaceholderText(/highlight/i)
    expect(highlightInputs).toHaveLength(1)
  })

  it('submits highlights as array', async () => {
    const user = userEvent.setup()

    render(
      <EntryForm
        fields={highlightsFieldConfig}
        onSubmit={mockOnSubmit}
        onCancel={mockOnCancel}
      />
    )

    await user.type(screen.getByLabelText(/title/i), 'Engineer')

    const addButton = screen.getByRole('button', { name: /add highlight/i })
    await user.click(addButton)
    await user.click(addButton)

    const highlightInputs = screen.getAllByPlaceholderText(/highlight/i)
    await user.type(highlightInputs[0], 'First highlight')
    await user.type(highlightInputs[1], 'Second highlight')

    await user.click(screen.getByRole('button', { name: /save/i }))

    await waitFor(() => {
      expect(mockOnSubmit).toHaveBeenCalledWith({
        title: 'Engineer',
        highlights: ['First highlight', 'Second highlight'],
      })
    })
  })

  it('pre-fills highlights from initial data', () => {
    const initialData = {
      title: 'Engineer',
      highlights: ['Highlight one', 'Highlight two', 'Highlight three'],
    }

    render(
      <EntryForm
        fields={highlightsFieldConfig}
        initialData={initialData}
        onSubmit={mockOnSubmit}
        onCancel={mockOnCancel}
      />
    )

    const highlightInputs = screen.getAllByPlaceholderText(/highlight/i)
    expect(highlightInputs).toHaveLength(3)
    expect(highlightInputs[0]).toHaveValue('Highlight one')
    expect(highlightInputs[1]).toHaveValue('Highlight two')
    expect(highlightInputs[2]).toHaveValue('Highlight three')
  })

  it('handles empty highlights array in submission', async () => {
    const user = userEvent.setup()

    render(
      <EntryForm
        fields={highlightsFieldConfig}
        onSubmit={mockOnSubmit}
        onCancel={mockOnCancel}
      />
    )

    await user.type(screen.getByLabelText(/title/i), 'Engineer')
    await user.click(screen.getByRole('button', { name: /save/i }))

    await waitFor(() => {
      expect(mockOnSubmit).toHaveBeenCalledWith({
        title: 'Engineer',
        highlights: [],
      })
    })
  })
})
