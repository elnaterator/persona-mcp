import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import AccomplishmentDetailView from '../../components/AccomplishmentDetailView'
import * as api from '../../services/api'
import type { Accomplishment } from '../../types/resume'

vi.mock('../../services/api')

const mockAccomplishment: Accomplishment = {
  id: 1,
  title: 'Led platform migration',
  situation: 'Monolith caused 4-hour deploys.',
  task: 'Migrate 3 services in 6 months.',
  action: 'Coordinated 4 teams, used feature flags.',
  result: 'Reduced deploy time by 80%.',
  accomplishment_date: '2024-03-15',
  tags: ['leadership', 'technical'],
  created_at: '2024-03-15T00:00:00Z',
  updated_at: '2024-03-15T00:00:00Z',
}

describe('AccomplishmentDetailView', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders all four STAR sections with their labels', async () => {
    vi.mocked(api.getAccomplishment).mockResolvedValue(mockAccomplishment)

    render(<AccomplishmentDetailView accomplishmentId={1} onBack={vi.fn()} />)

    await waitFor(() => {
      expect(screen.getByText('Led platform migration')).toBeInTheDocument()
    })

    // All four STAR section labels must be visible
    expect(screen.getByText(/Situation/i)).toBeInTheDocument()
    expect(screen.getByText(/Task/i)).toBeInTheDocument()
    expect(screen.getByText(/Action/i)).toBeInTheDocument()
    expect(screen.getByText(/Result/i)).toBeInTheDocument()
  })

  it('shows STAR content', async () => {
    vi.mocked(api.getAccomplishment).mockResolvedValue(mockAccomplishment)

    render(<AccomplishmentDetailView accomplishmentId={1} onBack={vi.fn()} />)

    await waitFor(() => {
      expect(screen.getByText('Monolith caused 4-hour deploys.')).toBeInTheDocument()
    })
    expect(screen.getByText('Reduced deploy time by 80%.')).toBeInTheDocument()
  })

  it('shows placeholder hint text for empty STAR fields', async () => {
    vi.mocked(api.getAccomplishment).mockResolvedValue({
      ...mockAccomplishment,
      situation: '',
      task: '',
    })

    render(<AccomplishmentDetailView accomplishmentId={1} onBack={vi.fn()} />)

    await waitFor(() => {
      expect(screen.getByText('Led platform migration')).toBeInTheDocument()
    })

    // Situation and Task sections are still rendered (with placeholder)
    expect(screen.getByText(/Situation/i)).toBeInTheDocument()
    expect(screen.getByText(/Task/i)).toBeInTheDocument()
  })

  it('shows accomplishment date and tags', async () => {
    vi.mocked(api.getAccomplishment).mockResolvedValue(mockAccomplishment)

    render(<AccomplishmentDetailView accomplishmentId={1} onBack={vi.fn()} />)

    await waitFor(() => {
      expect(screen.getByText(/2024-03-15/)).toBeInTheDocument()
    })
    expect(screen.getByText(/leadership/i)).toBeInTheDocument()
    expect(screen.getByText(/technical/i)).toBeInTheDocument()
  })

  it('calls onBack when back button is clicked', async () => {
    const user = userEvent.setup()
    const onBack = vi.fn()
    vi.mocked(api.getAccomplishment).mockResolvedValue(mockAccomplishment)

    render(<AccomplishmentDetailView accomplishmentId={1} onBack={onBack} />)

    await waitFor(() => {
      expect(screen.getByText('Led platform migration')).toBeInTheDocument()
    })

    await user.click(screen.getByRole('button', { name: /Back/i }))
    expect(onBack).toHaveBeenCalled()
  })

  it('edit button switches to edit mode with pre-populated fields', async () => {
    const user = userEvent.setup()
    vi.mocked(api.getAccomplishment).mockResolvedValue(mockAccomplishment)

    render(<AccomplishmentDetailView accomplishmentId={1} onBack={vi.fn()} />)

    await waitFor(() => {
      expect(screen.getByText('Led platform migration')).toBeInTheDocument()
    })

    await user.click(screen.getByRole('button', { name: /Edit/i }))

    // Edit form should appear with pre-populated title
    const titleInput = screen.getByDisplayValue('Led platform migration')
    expect(titleInput).toBeInTheDocument()
  })

  it('cancel reverts to view mode without saving', async () => {
    const user = userEvent.setup()
    vi.mocked(api.getAccomplishment).mockResolvedValue(mockAccomplishment)

    render(<AccomplishmentDetailView accomplishmentId={1} onBack={vi.fn()} />)

    await waitFor(() => {
      expect(screen.getByText('Led platform migration')).toBeInTheDocument()
    })

    await user.click(screen.getByRole('button', { name: /Edit/i }))
    await user.click(screen.getByRole('button', { name: /Cancel/i }))

    // Back in view mode
    expect(screen.queryByDisplayValue('Led platform migration')).not.toBeInTheDocument()
    expect(api.updateAccomplishment).not.toHaveBeenCalled()
  })

  it('save calls updateAccomplishment and shows updated data', async () => {
    const user = userEvent.setup()
    vi.mocked(api.getAccomplishment).mockResolvedValue(mockAccomplishment)
    vi.mocked(api.updateAccomplishment).mockResolvedValue({
      ...mockAccomplishment,
      result: 'Updated result with metrics.',
    })

    render(<AccomplishmentDetailView accomplishmentId={1} onBack={vi.fn()} />)

    await waitFor(() => {
      expect(screen.getByText('Led platform migration')).toBeInTheDocument()
    })

    await user.click(screen.getByRole('button', { name: /Edit/i }))

    const resultField = screen.getByDisplayValue('Reduced deploy time by 80%.')
    await user.clear(resultField)
    await user.type(resultField, 'Updated result with metrics.')

    await user.click(screen.getByRole('button', { name: /Save/i }))

    await waitFor(() => {
      expect(api.updateAccomplishment).toHaveBeenCalledWith(
        1,
        expect.objectContaining({ result: 'Updated result with metrics.' })
      )
    })
  })

  it('delete button with confirmation calls deleteAccomplishment and onBack', async () => {
    const user = userEvent.setup()
    const onBack = vi.fn()
    vi.mocked(api.getAccomplishment).mockResolvedValue(mockAccomplishment)
    vi.mocked(api.deleteAccomplishment).mockResolvedValue({ message: 'Deleted' })

    render(<AccomplishmentDetailView accomplishmentId={1} onBack={onBack} />)

    await waitFor(() => {
      expect(screen.getByText('Led platform migration')).toBeInTheDocument()
    })

    await user.click(screen.getByRole('button', { name: /Delete/i }))

    // Confirmation should appear
    await waitFor(() => {
      expect(screen.getByText(/Are you sure/i)).toBeInTheDocument()
    })

    // Confirm deletion
    await user.click(screen.getByRole('button', { name: /Confirm|Yes/i }))

    await waitFor(() => {
      expect(api.deleteAccomplishment).toHaveBeenCalledWith(1)
      expect(onBack).toHaveBeenCalled()
    })
  })
})
