import { describe, it, expect, vi, beforeEach } from 'vitest'
import { screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router'
import HomeView from '../../pages/home/index'
import * as api from '../../services/api'
import { renderWithQuery } from '../test-utils'
import type { SearchResult } from '../../types'

vi.mock('../../services/api')
vi.mock('@clerk/clerk-react', () => ({
  useUser: () => ({ user: null }),
  APIKeys: () => null,
}))

const mockResults: SearchResult[] = [
  { type: 'note', id: 1, title: 'Python async', tags: ['python'], url: '/notes/1' },
  { type: 'note', id: 2, title: 'Go patterns', tags: ['go'], url: '/notes/2' },
  {
    type: 'accomplishment',
    id: 10,
    title: 'Launched product',
    subtitle: 'Q1 2025',
    snippet: 'reduced time to market',
    tags: [],
    url: '/accomplishments/10',
  },
]

function renderHome() {
  return renderWithQuery(
    <MemoryRouter>
      <HomeView />
    </MemoryRouter>
  )
}

function mockAllListApis() {
  vi.mocked(api.listResumes).mockResolvedValue([])
  vi.mocked(api.listApplications).mockResolvedValue([])
  vi.mocked(api.listNotes).mockResolvedValue([])
  vi.mocked(api.listAccomplishments).mockResolvedValue([])
  vi.mocked(api.listContacts).mockResolvedValue([])
  vi.mocked(api.listAllTags).mockResolvedValue([])
}

describe('HomeView — global search', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockAllListApis()
  })

  it('renders search bar on home page', async () => {
    vi.mocked(api.globalSearch).mockResolvedValue([])
    renderHome()
    expect(screen.getByRole('textbox')).toBeInTheDocument()
  })

  it('shows hint text when search is empty', async () => {
    vi.mocked(api.globalSearch).mockResolvedValue([])
    renderHome()
    expect(screen.getByText(/type to search/i)).toBeInTheDocument()
  })

  it('shows grouped results by type', async () => {
    const user = userEvent.setup()
    vi.mocked(api.globalSearch).mockResolvedValue(mockResults)
    renderHome()

    await user.type(screen.getByRole('textbox'), 'python')

    await waitFor(() => {
      expect(screen.getByText('Python async')).toBeInTheDocument()
    })
    expect(screen.getByText('Go patterns')).toBeInTheDocument()
    expect(screen.getByText('Launched product')).toBeInTheDocument()
  })

  it('renders results as links with correct hrefs', async () => {
    const user = userEvent.setup()
    vi.mocked(api.globalSearch).mockResolvedValue(mockResults)
    renderHome()

    await user.type(screen.getByRole('textbox'), 'python')

    await waitFor(() => {
      expect(screen.getByText('Python async')).toBeInTheDocument()
    })

    const noteLink = screen.getByRole('link', { name: /Python async/ })
    expect(noteLink).toHaveAttribute('href', '/notes/1')

    const accLink = screen.getByRole('link', { name: /Launched product/ })
    expect(accLink).toHaveAttribute('href', '/accomplishments/10')
  })

  it('renders subtitle when present', async () => {
    const user = userEvent.setup()
    vi.mocked(api.globalSearch).mockResolvedValue(mockResults)
    renderHome()

    await user.type(screen.getByRole('textbox'), 'python')

    await waitFor(() => {
      expect(screen.getByText('Q1 2025')).toBeInTheDocument()
    })
  })

  it('renders snippet when present', async () => {
    const user = userEvent.setup()
    vi.mocked(api.globalSearch).mockResolvedValue(mockResults)
    renderHome()

    await user.type(screen.getByRole('textbox'), 'python')

    await waitFor(() => {
      expect(screen.getByText('reduced time to market')).toBeInTheDocument()
    })
  })

  it('shows no results message when search returns empty', async () => {
    const user = userEvent.setup()
    vi.mocked(api.globalSearch).mockResolvedValue([])
    renderHome()

    await user.type(screen.getByRole('textbox'), 'xyznotfound')

    await waitFor(() => {
      expect(screen.getByText(/no results/i)).toBeInTheDocument()
    })
  })

  it('groups results in TYPE_ORDER (accomplishments before notes)', async () => {
    const user = userEvent.setup()
    vi.mocked(api.globalSearch).mockResolvedValue(mockResults)
    renderHome()

    await user.type(screen.getByRole('textbox'), 'python')

    await waitFor(() => {
      expect(screen.getByText('Launched product')).toBeInTheDocument()
    })

    const accEl = screen.getByText('Launched product')
    const noteEl = screen.getByText('Python async')
    // Accomplishment result renders before note result in DOM
    expect(
      accEl.compareDocumentPosition(noteEl) & Node.DOCUMENT_POSITION_FOLLOWING
    ).toBeTruthy()
  })
})
