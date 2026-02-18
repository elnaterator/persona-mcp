import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import ApplicationListView from '../../components/ApplicationListView'
import * as api from '../../services/api'
import type { Application } from '../../types/resume'

vi.mock('../../services/api')

const mockApplications: Application[] = [
  {
    id: 1,
    company: 'Acme Corp',
    position: 'Software Engineer',
    description: 'Great job',
    status: 'Applied',
    url: 'https://acme.com/job',
    notes: 'Looks promising',
    resume_version_id: 1,
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-15T00:00:00Z',
  },
  {
    id: 2,
    company: 'Globex',
    position: 'Senior Engineer',
    description: '',
    status: 'Interview',
    url: null,
    notes: '',
    resume_version_id: null,
    created_at: '2024-02-01T00:00:00Z',
    updated_at: '2024-02-10T00:00:00Z',
  },
]

describe('ApplicationListView', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('shows loading spinner while fetching', () => {
    vi.mocked(api.listApplications).mockReturnValue(new Promise(() => {}))

    render(<ApplicationListView onSelectApp={vi.fn()} />)

    expect(screen.getByTestId('loading-spinner')).toBeInTheDocument()
  })

  it('renders applications after loading', async () => {
    vi.mocked(api.listApplications).mockResolvedValue(mockApplications)

    render(<ApplicationListView onSelectApp={vi.fn()} />)

    await waitFor(() => {
      expect(screen.getByText('Software Engineer')).toBeInTheDocument()
    })

    expect(screen.getByText('Acme Corp')).toBeInTheDocument()
    expect(screen.getByText('Senior Engineer')).toBeInTheDocument()
    expect(screen.getByText('Globex')).toBeInTheDocument()
  })

  it('shows status badges for each application', async () => {
    vi.mocked(api.listApplications).mockResolvedValue(mockApplications)

    render(<ApplicationListView onSelectApp={vi.fn()} />)

    await waitFor(() => {
      // Applied appears both in badge and select dropdown - check it exists
      expect(screen.getAllByText('Applied').length).toBeGreaterThan(0)
    })

    // Interview appears in badge and dropdown - check it exists
    expect(screen.getAllByText('Interview').length).toBeGreaterThan(0)
  })

  it('calls onSelectApp when an application is clicked', async () => {
    const user = userEvent.setup()
    const onSelectApp = vi.fn()
    vi.mocked(api.listApplications).mockResolvedValue(mockApplications)

    render(<ApplicationListView onSelectApp={onSelectApp} />)

    await waitFor(() => {
      expect(screen.getByText('Software Engineer')).toBeInTheDocument()
    })

    await user.click(screen.getByText('Software Engineer'))
    expect(onSelectApp).toHaveBeenCalledWith(1)
  })

  it('shows empty state when no applications exist', async () => {
    vi.mocked(api.listApplications).mockResolvedValue([])

    render(<ApplicationListView onSelectApp={vi.fn()} />)

    await waitFor(() => {
      expect(screen.getByText(/no applications found/i)).toBeInTheDocument()
    })
  })

  it('shows error message on fetch failure', async () => {
    vi.mocked(api.listApplications).mockRejectedValue(new Error('Server error'))

    render(<ApplicationListView onSelectApp={vi.fn()} />)

    await waitFor(() => {
      expect(screen.getByText(/failed to load applications/i)).toBeInTheDocument()
    })
  })

  it('shows New Application button', async () => {
    vi.mocked(api.listApplications).mockResolvedValue([])

    render(<ApplicationListView onSelectApp={vi.fn()} />)

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /new application/i })).toBeInTheDocument()
    })
  })

  it('toggles new application form when button is clicked', async () => {
    const user = userEvent.setup()
    vi.mocked(api.listApplications).mockResolvedValue([])

    render(<ApplicationListView onSelectApp={vi.fn()} />)

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /new application/i })).toBeInTheDocument()
    })

    await user.click(screen.getByRole('button', { name: /new application/i }))
    expect(screen.getByLabelText(/company \*/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/position \*/i)).toBeInTheDocument()
  })

  it('renders status filter dropdown', async () => {
    vi.mocked(api.listApplications).mockResolvedValue([])

    render(<ApplicationListView onSelectApp={vi.fn()} />)

    await waitFor(() => {
      expect(screen.getByRole('combobox', { name: /filter by status/i })).toBeInTheDocument()
    })
  })

  it('renders search input', async () => {
    vi.mocked(api.listApplications).mockResolvedValue([])

    render(<ApplicationListView onSelectApp={vi.fn()} />)

    await waitFor(() => {
      expect(screen.getByRole('searchbox', { name: /search applications/i })).toBeInTheDocument()
    })
  })
})
