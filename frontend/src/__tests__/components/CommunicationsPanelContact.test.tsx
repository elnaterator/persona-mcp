import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import CommunicationsPanel from '../../components/CommunicationsPanel'
import * as api from '../../services/api'
import type { Communication } from '../../types'

vi.mock('../../services/api')

const mockComm: Communication = {
  id: 1,
  contact_ref_id: 42,
  type: 'email',
  direction: 'sent',
  subject: 'Hello',
  body: 'Test body',
  date: '2025-04-01',
  status: 'sent',
  tags: ['outreach'],
  created_at: '2025-04-01T00:00:00Z',
}

function renderPanel(parentType: 'application' | 'contact' = 'contact', parentId = 42) {
  return render(<CommunicationsPanel parentType={parentType} parentId={parentId} />)
}

describe('CommunicationsPanel (parentType=contact)', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.mocked(api.listAllTags).mockResolvedValue(['outreach', 'followup'])
    vi.mocked(api.listContactCommunications).mockResolvedValue([mockComm])
  })

  it('lists communications for a contact', async () => {
    renderPanel()
    await waitFor(() => {
      expect(screen.getByText('Hello')).toBeInTheDocument()
    })
    expect(screen.getByText('Test body')).toBeInTheDocument()
    expect(api.listContactCommunications).toHaveBeenCalledWith(42)
  })

  it('renders tag chips on comm row', async () => {
    renderPanel()
    await waitFor(() => {
      expect(screen.getByText('outreach')).toBeInTheDocument()
    })
  })

  it('add form calls addContactCommunication', async () => {
    const user = userEvent.setup()
    vi.mocked(api.addContactCommunication).mockResolvedValue({
      ...mockComm,
      id: 2,
      subject: 'New',
    })
    vi.mocked(api.listContactCommunications)
      .mockResolvedValueOnce([mockComm])
      .mockResolvedValue([mockComm, { ...mockComm, id: 2, subject: 'New' }])

    renderPanel()
    await waitFor(() => expect(screen.getByText('Hello')).toBeInTheDocument())

    await user.click(screen.getByRole('button', { name: /Add Communication/i }))
    const subjectInput = screen.getByPlaceholderText('Subject line')
    await user.clear(subjectInput)
    await user.type(subjectInput, 'New')
    const bodyTextarea = screen.getByPlaceholderText('Message body...')
    await user.type(bodyTextarea, 'body text')
    await user.click(screen.getByRole('button', { name: /Save/i }))

    await waitFor(() => {
      expect(api.addContactCommunication).toHaveBeenCalledWith(
        42,
        expect.objectContaining({ subject: 'New' })
      )
    })
  })

  it('delete calls removeContactCommunication', async () => {
    const user = userEvent.setup()
    vi.mocked(api.removeContactCommunication).mockResolvedValue({ message: 'ok' })
    vi.mocked(api.listContactCommunications)
      .mockResolvedValueOnce([mockComm])
      .mockResolvedValue([])

    renderPanel()
    await waitFor(() => expect(screen.getByText('Hello')).toBeInTheDocument())

    await user.click(screen.getByRole('button', { name: /Delete communication/i }))
    await user.click(screen.getByRole('button', { name: /Confirm/i }))

    await waitFor(() => {
      expect(api.removeContactCommunication).toHaveBeenCalledWith(42, 1)
    })
  })
})

describe('CommunicationsPanel (parentType=application)', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.mocked(api.listAllTags).mockResolvedValue([])
    vi.mocked(api.listCommunications).mockResolvedValue([
      { ...mockComm, app_id: 99, contact_ref_id: undefined },
    ])
  })

  it('calls listCommunications for application parent', async () => {
    renderPanel('application', 99)
    await waitFor(() => {
      expect(api.listCommunications).toHaveBeenCalledWith(99)
    })
  })
})
