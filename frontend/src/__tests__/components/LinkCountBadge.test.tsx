/**
 * Tests that link_count badges render correctly in list views.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router'
import NoteListView from '../../components/NoteListView'
import * as api from '../../services/api'
import type { NoteSummary } from '../../types/resume'

vi.mock('../../services/api')

function renderNoteList() {
  return render(
    <MemoryRouter>
      <NoteListView />
    </MemoryRouter>
  )
}

describe('link_count badge', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.mocked(api.listAllTags).mockResolvedValue([])
  })

  it('shows link count badge when link_count > 0', async () => {
    const notes: NoteSummary[] = [
      {
        id: 1,
        title: 'Linked Note',
        tags: [],
        created_at: '2026-01-01T00:00:00Z',
        updated_at: '2026-01-01T00:00:00Z',
        link_count: 3,
      },
    ]
    vi.mocked(api.listNotes).mockResolvedValue(notes)
    renderNoteList()
    await waitFor(() => {
      expect(screen.getByText('Linked Note')).toBeInTheDocument()
    })
    expect(screen.getByText(/🔗 3/)).toBeInTheDocument()
  })

  it('hides badge when link_count is 0 or absent', async () => {
    const notes: NoteSummary[] = [
      {
        id: 2,
        title: 'Lonely Note',
        tags: [],
        created_at: '2026-01-01T00:00:00Z',
        updated_at: '2026-01-01T00:00:00Z',
        link_count: 0,
      },
    ]
    vi.mocked(api.listNotes).mockResolvedValue(notes)
    renderNoteList()
    await waitFor(() => {
      expect(screen.getByText('Lonely Note')).toBeInTheDocument()
    })
    expect(screen.queryByText(/🔗/)).not.toBeInTheDocument()
  })
})
