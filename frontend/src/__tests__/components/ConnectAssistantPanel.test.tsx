/**
 * Tests the connect panel's per-assistant setup instructions.
 */
import { describe, it, expect, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import ConnectAssistantPanel from '../../components/ConnectAssistantPanel'

async function openPanel() {
  render(<ConnectAssistantPanel />)
  await userEvent.click(screen.getByRole('button', { name: /connect your ai assistant/i }))
}

describe('ConnectAssistantPanel', () => {
  beforeEach(() => {
    Object.defineProperty(window, 'location', {
      value: new URL('https://pktx.test/'),
      writable: true,
    })
  })

  it('shows the MCP server URL for the default assistant', async () => {
    await openPanel()
    expect(screen.getByText(/\/mcp$/)).toBeInTheDocument()
  })

  it('shows ChatGPT developer mode steps when ChatGPT is selected', async () => {
    await openPanel()
    await userEvent.selectOptions(screen.getByLabelText('Assistant'), 'chatgpt')
    expect(screen.getByText(/turn on Developer mode/)).toBeInTheDocument()
    expect(screen.getByText(/Plugins → Create/)).toBeInTheDocument()
  })

  it('lists ChatGPT plan and naming caveats as notes', async () => {
    await openPanel()
    await userEvent.selectOptions(screen.getByLabelText('Assistant'), 'chatgpt')
    expect(screen.getByText(/Plus, Pro, Business, Enterprise, or Education plan/)).toBeInTheDocument()
    expect(screen.getByText(/label the section Connectors/)).toBeInTheDocument()
  })

  it('shows no notes for assistants that need none', async () => {
    await openPanel()
    await userEvent.selectOptions(screen.getByLabelText('Assistant'), 'claude-code')
    expect(screen.queryByText(/Developer mode/)).not.toBeInTheDocument()
  })
})
