import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router'
import NoteListView from '../../components/NoteListView'
import * as api from '../../services/api'
import type { NoteSummary } from '../../types/resume'

vi.mock('../../services/api')

const mockSummaries: NoteSummary[] = [
  {
    id: 1,
    title: 'Python async patterns',
    tags: ['python', 'async'],
    created_at: '2026-03-26T10:00:00Z',
    updated_at: '2026-03-26T14:30:00Z',
  },
  {
    id: 2,
    title: 'Go concurrency',
    tags: ['go'],
    created_at: '2026-03-25T10:00:00Z',
    updated_at: '2026-03-25T10:00:00Z',
  },
]

function renderView() {
  return render(
    <MemoryRouter>
      <NoteListView />
    </MemoryRouter>
  )
}

describe('NoteListView', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders notes after loading', async () => {
    vi.mocked(api.listNotes).mockResolvedValue(mockSummaries)
    vi.mocked(api.listNoteTags).mockResolvedValue(['async', 'go', 'python'])
    vi.mocked(api.listAccomplishmentTags).mockResolvedValue([])
    renderView()
    await waitFor(() => {
      expect(screen.getByText('Python async patterns')).toBeInTheDocument()
    })
    expect(screen.getByText('Go concurrency')).toBeInTheDocument()
  })

  it('shows empty state when no notes', async () => {
    vi.mocked(api.listNotes).mockResolvedValue([])
    vi.mocked(api.listNoteTags).mockResolvedValue([])
    vi.mocked(api.listAccomplishmentTags).mockResolvedValue([])
    renderView()
    await waitFor(() => {
      expect(screen.queryByText('Python async patterns')).not.toBeInTheDocument()
    })
  })

  it('renders each note as a link to its detail page', async () => {
    vi.mocked(api.listNotes).mockResolvedValue(mockSummaries)
    vi.mocked(api.listNoteTags).mockResolvedValue(['async', 'go', 'python'])
    vi.mocked(api.listAccomplishmentTags).mockResolvedValue([])
    renderView()
    await waitFor(() => {
      expect(screen.getByText('Python async patterns')).toBeInTheDocument()
    })
    const links = screen.getAllByRole('link')
    const noteLinks = links.filter((l) => l.getAttribute('href')?.startsWith('/notes/'))
    expect(noteLinks.length).toBe(2)
    expect(noteLinks[0]).toHaveAttribute('href', '/notes/1')
    expect(noteLinks[1]).toHaveAttribute('href', '/notes/2')
  })

  it('has New Note button that reveals create form', async () => {
    const user = userEvent.setup()
    vi.mocked(api.listNotes).mockResolvedValue([])
    vi.mocked(api.listNoteTags).mockResolvedValue([])
    vi.mocked(api.listAccomplishmentTags).mockResolvedValue([])
    renderView()
    await waitFor(() => {
      expect(screen.getByRole('button', { name: /New Note/i })).toBeInTheDocument()
    })
    await user.click(screen.getByRole('button', { name: /New Note/i }))
    expect(screen.getByLabelText(/Title/i)).toBeInTheDocument()
  })

  it('form has labeled inputs for title and content', async () => {
    const user = userEvent.setup()
    vi.mocked(api.listNotes).mockResolvedValue([])
    vi.mocked(api.listNoteTags).mockResolvedValue([])
    vi.mocked(api.listAccomplishmentTags).mockResolvedValue([])
    renderView()
    await waitFor(() => {
      expect(screen.getByRole('button', { name: /New Note/i })).toBeInTheDocument()
    })
    await user.click(screen.getByRole('button', { name: /New Note/i }))
    expect(screen.getByLabelText(/Title/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/Content/i)).toBeInTheDocument()
  })

  it('submitting with no title shows an error', async () => {
    const user = userEvent.setup()
    vi.mocked(api.listNotes).mockResolvedValue([])
    vi.mocked(api.listNoteTags).mockResolvedValue([])
    vi.mocked(api.listAccomplishmentTags).mockResolvedValue([])
    renderView()
    await waitFor(() => {
      expect(screen.getByRole('button', { name: /New Note/i })).toBeInTheDocument()
    })
    await user.click(screen.getByRole('button', { name: /New Note/i }))
    const saveButton = screen.getByRole('button', { name: /Save/i })
    await user.click(saveButton)
    expect(screen.getByText(/[Tt]itle.*required|required.*[Tt]itle/i)).toBeInTheDocument()
  })

  it('calls createNote and reloads list on valid submit', async () => {
    const user = userEvent.setup()
    vi.mocked(api.listNotes).mockResolvedValue([])
    vi.mocked(api.listNoteTags).mockResolvedValue([])
    vi.mocked(api.listAccomplishmentTags).mockResolvedValue([])
    vi.mocked(api.createNote).mockResolvedValue({
      id: 99,
      title: 'New note',
      content: '',
      tags: [],
      created_at: '2026-01-01T00:00:00Z',
      updated_at: '2026-01-01T00:00:00Z',
    })
    renderView()
    await waitFor(() => {
      expect(screen.getByRole('button', { name: /New Note/i })).toBeInTheDocument()
    })
    await user.click(screen.getByRole('button', { name: /New Note/i }))
    await user.type(screen.getByLabelText(/Title/i), 'New note')
    await user.click(screen.getByRole('button', { name: /Save/i }))
    await waitFor(() => {
      expect(api.createNote).toHaveBeenCalledWith(
        expect.objectContaining({ title: 'New note' })
      )
    })
  })
})
