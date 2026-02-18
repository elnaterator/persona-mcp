import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import ResumeListView from '../../components/ResumeListView'
import * as api from '../../services/api'
import type { ResumeVersionSummary } from '../../types/resume'

vi.mock('../../services/api')

const mockVersions: ResumeVersionSummary[] = [
  {
    id: 1,
    label: 'Default Resume',
    is_default: true,
    app_count: 3,
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z',
  },
  {
    id: 2,
    label: 'Senior Engineer Version',
    is_default: false,
    app_count: 1,
    created_at: '2024-02-01T00:00:00Z',
    updated_at: '2024-02-01T00:00:00Z',
  },
]

describe('ResumeListView', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('shows loading spinner while fetching', () => {
    vi.mocked(api.listResumes).mockReturnValue(new Promise(() => {}))

    render(<ResumeListView onSelectResume={vi.fn()} />)

    expect(screen.getByTestId('loading-spinner')).toBeInTheDocument()
  })

  it('renders resume versions after loading', async () => {
    vi.mocked(api.listResumes).mockResolvedValue(mockVersions)

    render(<ResumeListView onSelectResume={vi.fn()} />)

    await waitFor(() => {
      expect(screen.getByText('Default Resume')).toBeInTheDocument()
    })

    expect(screen.getByText('Senior Engineer Version')).toBeInTheDocument()
  })

  it('shows default badge on the default version', async () => {
    vi.mocked(api.listResumes).mockResolvedValue(mockVersions)

    render(<ResumeListView onSelectResume={vi.fn()} />)

    await waitFor(() => {
      expect(screen.getByText('Default')).toBeInTheDocument()
    })
  })

  it('shows app count for each version', async () => {
    vi.mocked(api.listResumes).mockResolvedValue(mockVersions)

    render(<ResumeListView onSelectResume={vi.fn()} />)

    await waitFor(() => {
      expect(screen.getByText(/3 applications/i)).toBeInTheDocument()
    })
    expect(screen.getByText(/1 application$/)).toBeInTheDocument()
  })

  it('calls onSelectResume when a version is clicked', async () => {
    const user = userEvent.setup()
    const onSelectResume = vi.fn()
    vi.mocked(api.listResumes).mockResolvedValue(mockVersions)

    render(<ResumeListView onSelectResume={onSelectResume} />)

    await waitFor(() => {
      expect(screen.getByText('Default Resume')).toBeInTheDocument()
    })

    await user.click(screen.getByText('Default Resume'))
    expect(onSelectResume).toHaveBeenCalledWith(1)
  })

  it('shows Set as Default button for non-default versions', async () => {
    vi.mocked(api.listResumes).mockResolvedValue(mockVersions)

    render(<ResumeListView onSelectResume={vi.fn()} />)

    await waitFor(() => {
      expect(screen.getByText('Senior Engineer Version')).toBeInTheDocument()
    })

    // Use getAllByRole since the li with role=button may also be matched
    const setDefaultBtns = screen.getAllByRole('button', { name: /set as default/i })
    expect(setDefaultBtns.length).toBeGreaterThan(0)
  })

  it('disables delete button when only one version exists', async () => {
    vi.mocked(api.listResumes).mockResolvedValue([mockVersions[0]])

    render(<ResumeListView onSelectResume={vi.fn()} />)

    await waitFor(() => {
      expect(screen.getByText('Default Resume')).toBeInTheDocument()
    })

    // Use getAllByRole since there may be multiple (li element has role=button too)
    const deleteBtns = screen.getAllByRole('button', { name: /delete/i })
    // The actual button element (not the li) should be disabled
    const actualDeleteBtn = deleteBtns.find((el) => el.tagName === 'BUTTON')
    expect(actualDeleteBtn).toBeDefined()
    expect(actualDeleteBtn).toBeDisabled()
  })

  it('shows empty state when no versions exist', async () => {
    vi.mocked(api.listResumes).mockResolvedValue([])

    render(<ResumeListView onSelectResume={vi.fn()} />)

    await waitFor(() => {
      expect(screen.getByText(/no resume versions found/i)).toBeInTheDocument()
    })
  })

  it('shows error message on fetch failure', async () => {
    vi.mocked(api.listResumes).mockRejectedValue(new Error('Server error'))

    render(<ResumeListView onSelectResume={vi.fn()} />)

    await waitFor(() => {
      expect(screen.getByText(/failed to load resume versions/i)).toBeInTheDocument()
    })
  })
})
