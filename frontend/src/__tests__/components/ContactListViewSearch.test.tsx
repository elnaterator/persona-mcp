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

describe('ContactListView — unified search', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.mocked(api.listContacts).mockResolvedValue([])
    vi.mocked(api.listAllTags).mockResolvedValue(['outreach', 'followup'])
    vi.mocked(api.searchCommunications).mockResolvedValue([])
  })

  it('shows a single search bar covering contacts and communications', async () => {
    renderView()
    await waitFor(() => {
      expect(screen.getByPlaceholderText(/Search contacts and communications/i)).toBeInTheDocument()
    })
    expect(screen.queryByText(/Search Communications/i)).not.toBeInTheDocument()
  })

  it('does not query communications until there is input', async () => {
    renderView()
    await waitFor(() => expect(api.listContacts).toHaveBeenCalled())
    expect(api.searchCommunications).not.toHaveBeenCalled()
  })

  it('calls searchCommunications and listContacts with the same debounced query', async () => {
    const user = userEvent.setup()
    vi.mocked(api.searchCommunications).mockResolvedValue([mockResult])

    renderView()
    const input = await screen.findByPlaceholderText(/Search contacts and communications/i)
    await user.type(input, 'Intro')

    await waitFor(
      () => {
        expect(api.searchCommunications).toHaveBeenCalledWith(
          expect.objectContaining({ q: 'Intro' })
        )
        expect(api.listContacts).toHaveBeenCalledWith(undefined, 'Intro')
      },
      { timeout: 1000 }
    )
  })

  it('renders communication search results', async () => {
    const user = userEvent.setup()
    vi.mocked(api.searchCommunications).mockResolvedValue([mockResult])

    renderView()
    const input = await screen.findByPlaceholderText(/Search contacts and communications/i)
    await user.type(input, 'Intro')

    await waitFor(
      () => {
        expect(screen.getByText('Intro message')).toBeInTheDocument()
        expect(screen.getByText('Alice Smith')).toBeInTheDocument()
      },
      { timeout: 1000 }
    )
  })
})
