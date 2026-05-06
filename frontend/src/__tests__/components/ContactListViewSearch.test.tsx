import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router'
import ContactListView from '../../pages/contacts/ContactListView'
import * as api from '../../services/api'
import type { CommunicationSearchResult } from '../../types'

vi.mock('../../services/api')

const mockResult: CommunicationSearchResult = {
  id: 1,
  parentType: 'contact',
  parentId: 10,
  parentName: 'Alice Smith',
  type: 'email',
  direction: 'sent',
  subject: 'Intro message',
  body: 'body here',
  date: '2025-04-01',
  status: 'sent',
  tags: ['outreach'],
  created_at: '2025-04-01T00:00:00Z',
}

function renderView() {
  return render(
    <MemoryRouter>
      <ContactListView />
    </MemoryRouter>
  )
}

describe('ContactListView — communication search panel', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.mocked(api.listContacts).mockResolvedValue([])
    vi.mocked(api.listAllTags).mockResolvedValue(['outreach', 'followup'])
    vi.mocked(api.searchCommunications).mockResolvedValue([])
  })

  it('shows "Search Communications" toggle', async () => {
    renderView()
    await waitFor(() => {
      expect(screen.getByText(/Search Communications/i)).toBeInTheDocument()
    })
  })

  it('expands search panel on toggle click', async () => {
    const user = userEvent.setup()
    renderView()
    await waitFor(() => expect(screen.getByText(/Search Communications/i)).toBeInTheDocument())

    await user.click(screen.getByText(/Search Communications/i))
    expect(screen.getByPlaceholderText(/Search subject/i)).toBeInTheDocument()
  })

  it('calls searchCommunications with debounced query', async () => {
    const user = userEvent.setup()
    vi.mocked(api.searchCommunications).mockResolvedValue([mockResult])

    renderView()
    await waitFor(() => expect(screen.getByText(/Search Communications/i)).toBeInTheDocument())
    await user.click(screen.getByText(/Search Communications/i))

    const input = screen.getByPlaceholderText(/Search subject/i)
    await user.type(input, 'Intro')

    await waitFor(
      () => {
        expect(api.searchCommunications).toHaveBeenCalledWith(
          expect.objectContaining({ q: 'Intro' })
        )
      },
      { timeout: 1000 }
    )
  })

  it('renders search results', async () => {
    const user = userEvent.setup()
    vi.mocked(api.searchCommunications).mockResolvedValue([mockResult])

    renderView()
    await waitFor(() => expect(screen.getByText(/Search Communications/i)).toBeInTheDocument())
    await user.click(screen.getByText(/Search Communications/i))

    const input = screen.getByPlaceholderText(/Search subject/i)
    await user.type(input, 'Intro')

    await waitFor(
      () => {
        expect(screen.getByText('Intro message')).toBeInTheDocument()
        expect(screen.getByText('Alice Smith')).toBeInTheDocument()
      },
      { timeout: 1000 }
    )
  })

  it('parent filter buttons are rendered', async () => {
    const user = userEvent.setup()
    renderView()
    await waitFor(() => expect(screen.getByText(/Search Communications/i)).toBeInTheDocument())
    await user.click(screen.getByText(/Search Communications/i))

    expect(screen.getByRole('button', { name: /^All$/i })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /Applications/i })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /Contacts/i })).toBeInTheDocument()
  })
})
