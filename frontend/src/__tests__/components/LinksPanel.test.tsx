import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router'
import { LinksPanel } from '../../components/LinksPanel'
import * as api from '../../services/api'
import type { GroupedLinks } from '../../types'

vi.mock('../../services/api')

// LinkPickerModal fetches from all list endpoints
vi.mock('../../components/LinkPickerModal', () => ({
  LinkPickerModal: ({ onClose }: { onClose: () => void }) => (
    <div data-testid="link-picker-modal">
      <button onClick={onClose}>Close</button>
    </div>
  ),
}))

function renderPanel(links: GroupedLinks = {}, onChange = vi.fn()) {
  return render(
    <MemoryRouter>
      <LinksPanel
        resourceType="note"
        resourceId={1}
        links={links}
        onChange={onChange}
      />
    </MemoryRouter>
  )
}

describe('LinksPanel', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('shows empty state when no links', () => {
    renderPanel({})
    expect(screen.getByText(/No links yet/i)).toBeInTheDocument()
  })

  it('shows link count in header', () => {
    const links: GroupedLinks = {
      application: [{ type: 'application', id: 10, name: 'Acme – Dev' }],
    }
    renderPanel(links)
    expect(screen.getByText(/Links \(1\)/i)).toBeInTheDocument()
  })

  it('renders linked resource names', () => {
    const links: GroupedLinks = {
      application: [{ type: 'application', id: 10, name: 'Acme Corp' }],
    }
    renderPanel(links)
    expect(screen.getByText('Acme Corp')).toBeInTheDocument()
  })

  it('renders type section label', () => {
    const links: GroupedLinks = {
      application: [{ type: 'application', id: 10, name: 'Acme Corp' }],
    }
    renderPanel(links)
    expect(screen.getByText('Applications')).toBeInTheDocument()
  })

  it('calls unlinkResources and onChange when unlink button clicked', async () => {
    const user = userEvent.setup()
    vi.mocked(api.unlinkResources).mockResolvedValue(undefined)
    const onChange = vi.fn()
    const links: GroupedLinks = {
      application: [{ type: 'application', id: 10, name: 'Acme Corp' }],
    }
    renderPanel(links, onChange)
    const unlinkBtn = screen.getByRole('button', { name: /Unlink Acme Corp/i })
    await user.click(unlinkBtn)
    await waitFor(() => {
      expect(api.unlinkResources).toHaveBeenCalledWith('note', 1, 'application', 10)
      expect(onChange).toHaveBeenCalled()
    })
  })

  it('opens link picker modal on Link button click', async () => {
    const user = userEvent.setup()
    renderPanel({})
    await user.click(screen.getByRole('button', { name: /Link/i }))
    expect(screen.getByTestId('link-picker-modal')).toBeInTheDocument()
  })

  it('closes modal when onClose triggered', async () => {
    const user = userEvent.setup()
    renderPanel({})
    await user.click(screen.getByRole('button', { name: /Link/i }))
    expect(screen.getByTestId('link-picker-modal')).toBeInTheDocument()
    await user.click(screen.getByRole('button', { name: /Close/i }))
    expect(screen.queryByTestId('link-picker-modal')).not.toBeInTheDocument()
  })

  it('shows multiple type groups', () => {
    const links: GroupedLinks = {
      application: [{ type: 'application', id: 1, name: 'App One' }],
      contact: [{ type: 'contact', id: 2, name: 'Jane Doe' }],
    }
    renderPanel(links)
    expect(screen.getByText('Applications')).toBeInTheDocument()
    expect(screen.getByText('Contacts')).toBeInTheDocument()
    expect(screen.getByText('App One')).toBeInTheDocument()
    expect(screen.getByText('Jane Doe')).toBeInTheDocument()
    expect(screen.getByText(/Links \(2\)/i)).toBeInTheDocument()
  })
})
