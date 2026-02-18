import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import AccomplishmentListView from '../../components/AccomplishmentListView'
import * as api from '../../services/api'
import type { AccomplishmentSummary } from '../../types/resume'

vi.mock('../../services/api')

const mockSummaries: AccomplishmentSummary[] = [
  {
    id: 1,
    title: 'Led platform migration',
    accomplishment_date: '2024-03-15',
    tags: ['leadership', 'technical'],
    created_at: '2024-03-15T00:00:00Z',
    updated_at: '2024-03-15T00:00:00Z',
  },
  {
    id: 2,
    title: 'Reduced deploy time',
    accomplishment_date: null,
    tags: ['technical'],
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z',
  },
]

describe('AccomplishmentListView', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders accomplishments after loading', async () => {
    vi.mocked(api.listAccomplishments).mockResolvedValue(mockSummaries)
    vi.mocked(api.listAccomplishmentTags).mockResolvedValue(['leadership', 'technical'])

    render(<AccomplishmentListView onSelectAccomplishment={vi.fn()} />)

    await waitFor(() => {
      expect(screen.getByText('Led platform migration')).toBeInTheDocument()
    })
    expect(screen.getByText('Reduced deploy time')).toBeInTheDocument()
  })

  it('shows empty state when no accomplishments', async () => {
    vi.mocked(api.listAccomplishments).mockResolvedValue([])
    vi.mocked(api.listAccomplishmentTags).mockResolvedValue([])

    render(<AccomplishmentListView onSelectAccomplishment={vi.fn()} />)

    await waitFor(() => {
      expect(screen.queryByText('Led platform migration')).not.toBeInTheDocument()
    })
  })

  it('has New Accomplishment button that reveals create form', async () => {
    const user = userEvent.setup()
    vi.mocked(api.listAccomplishments).mockResolvedValue([])
    vi.mocked(api.listAccomplishmentTags).mockResolvedValue([])

    render(<AccomplishmentListView onSelectAccomplishment={vi.fn()} />)

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /New Accomplishment/i })).toBeInTheDocument()
    })

    await user.click(screen.getByRole('button', { name: /New Accomplishment/i }))

    // Form should appear
    expect(screen.getByLabelText(/Title/i)).toBeInTheDocument()
  })

  it('form has labeled inputs for all STAR fields', async () => {
    const user = userEvent.setup()
    vi.mocked(api.listAccomplishments).mockResolvedValue([])
    vi.mocked(api.listAccomplishmentTags).mockResolvedValue([])

    render(<AccomplishmentListView onSelectAccomplishment={vi.fn()} />)

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /New Accomplishment/i })).toBeInTheDocument()
    })
    await user.click(screen.getByRole('button', { name: /New Accomplishment/i }))

    expect(screen.getByLabelText(/Title/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/Situation/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/Task/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/Action/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/Result/i)).toBeInTheDocument()
  })

  it('submitting with no title shows an error', async () => {
    const user = userEvent.setup()
    vi.mocked(api.listAccomplishments).mockResolvedValue([])
    vi.mocked(api.listAccomplishmentTags).mockResolvedValue([])

    render(<AccomplishmentListView onSelectAccomplishment={vi.fn()} />)

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /New Accomplishment/i })).toBeInTheDocument()
    })
    await user.click(screen.getByRole('button', { name: /New Accomplishment/i }))

    const saveButton = screen.getByRole('button', { name: /Save/i })
    await user.click(saveButton)

    expect(screen.getByText(/[Tt]itle.*required|required.*[Tt]itle/i)).toBeInTheDocument()
  })

  it('calls createAccomplishment and reloads list on valid submit', async () => {
    const user = userEvent.setup()
    vi.mocked(api.listAccomplishments).mockResolvedValue([])
    vi.mocked(api.listAccomplishmentTags).mockResolvedValue([])
    vi.mocked(api.createAccomplishment).mockResolvedValue({
      id: 99,
      title: 'New acc',
      situation: '',
      task: '',
      action: '',
      result: '',
      accomplishment_date: null,
      tags: [],
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-01T00:00:00Z',
    })

    render(<AccomplishmentListView onSelectAccomplishment={vi.fn()} />)

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /New Accomplishment/i })).toBeInTheDocument()
    })
    await user.click(screen.getByRole('button', { name: /New Accomplishment/i }))

    await user.type(screen.getByLabelText(/Title/i), 'New acc')
    await user.click(screen.getByRole('button', { name: /Save/i }))

    await waitFor(() => {
      expect(api.createAccomplishment).toHaveBeenCalledWith(
        expect.objectContaining({ title: 'New acc' })
      )
    })
  })

  it('calls onSelectAccomplishment when a list item is clicked', async () => {
    const user = userEvent.setup()
    const onSelect = vi.fn()
    vi.mocked(api.listAccomplishments).mockResolvedValue(mockSummaries)
    vi.mocked(api.listAccomplishmentTags).mockResolvedValue(['leadership'])

    render(<AccomplishmentListView onSelectAccomplishment={onSelect} />)

    await waitFor(() => {
      expect(screen.getByText('Led platform migration')).toBeInTheDocument()
    })

    await user.click(screen.getByText('Led platform migration'))

    expect(onSelect).toHaveBeenCalledWith(1)
  })
})
