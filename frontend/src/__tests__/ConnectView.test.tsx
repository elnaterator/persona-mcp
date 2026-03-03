/**
 * ConnectView tests — T008 (Phase 3) + T014/T015 (Phase 4) + T018/T020 (Phase 6),
 * 011-mcp-instructions
 *
 * Tests cover:
 * - Connect tab content renders
 * - APIKeys section renders (or custom fallback)
 * - Paste-input field renders
 * - Config snippets show YOUR_API_KEY placeholder (per active tab, T018)
 * - Config snippets substitute real key (per active tab, T018)
 * - Warning banner is visible when keyJustCreated=true (post-creation event)
 * - Warning banner is absent when not in keyJustCreated state
 * - Warning banner is dismissable
 * - Tab navigation — 4 tabs rendered, correct content per tab (T018/T020)
 * - Copy buttons per-assistant (T014/T015): call clipboard.writeText with real key
 * - Copy button shows "Copied!" feedback then reverts (T015)
 * - Regression: Navigation tab buttons for Resumes, Applications, Accomplishments (FR-012)
 */

import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import ConnectView from '../components/ConnectView'
import Navigation from '../components/Navigation'

// Mock @clerk/clerk-react — we don't need a real Clerk provider in unit tests
vi.mock('@clerk/clerk-react', () => ({
  APIKeys: () => <div data-testid="api-keys-component">APIKeys</div>,
  useClerk: vi.fn(() => ({
    apiKeys: {
      create: vi.fn(),
    },
  })),
}))

describe('ConnectView', () => {
  describe('initial render', () => {
    it('renders the Connect tab heading or content', () => {
      render(<ConnectView />)
      expect(
        screen.getByRole('heading', { level: 2, hidden: true }) ||
          screen.getByText(/connect/i) ||
          screen.getByText(/ai coding assistant/i),
      ).toBeInTheDocument()
    })

    it('renders the APIKeys section', () => {
      render(<ConnectView />)
      expect(screen.getByTestId('api-keys-component')).toBeInTheDocument()
    })

    it('renders the paste-input field for API key', () => {
      render(<ConnectView />)
      const input =
        screen.getByLabelText(/paste.*api key/i) ||
        screen.getByPlaceholderText(/paste.*api key/i) ||
        screen.getByRole('textbox', { name: /api key/i })
      expect(input).toBeInTheDocument()
    })

    it('shows YOUR_API_KEY placeholder in each tab snippet when input is empty', async () => {
      const user = userEvent.setup()
      render(<ConnectView />)

      // Verify each assistant tab's snippet shows the placeholder
      for (const name of ['Claude Code', 'Cursor', 'GitHub Copilot', 'Amazon Kiro']) {
        await user.click(screen.getByRole('tab', { name: new RegExp(name, 'i') }))
        expect(screen.getByText(/YOUR_API_KEY/)).toBeInTheDocument()
      }
    })

    it('shows static API key tip on initial render', () => {
      render(<ConnectView />)
      expect(screen.getByText(/when you create an api key, copy it immediately/i)).toBeInTheDocument()
    })
  })

  describe('key substitution in config snippets', () => {
    it('substitutes real key in all 4 snippets when user pastes a key', async () => {
      const user = userEvent.setup()
      render(<ConnectView />)

      const input = screen.getByRole('textbox', { name: /api key/i })
      await user.clear(input)
      await user.type(input, 'ak_live_testkey12345')

      // Verify each tab shows the real key and no placeholder
      for (const name of ['Claude Code', 'Cursor', 'GitHub Copilot', 'Amazon Kiro']) {
        await user.click(screen.getByRole('tab', { name: new RegExp(name, 'i') }))
        expect(screen.getByText(/ak_live_testkey12345/)).toBeInTheDocument()
        expect(screen.queryByText(/YOUR_API_KEY/)).not.toBeInTheDocument()
      }
    })
  })

  describe('APIKeys error boundary', () => {
    it('renders fallback message when APIKeys throws (e.g. API keys disabled)', async () => {
      // Make the mocked APIKeys throw to simulate Clerk's error
      const clerkMock = await import('@clerk/clerk-react')
      const originalAPIKeys = clerkMock.APIKeys
      vi.mocked(clerkMock).APIKeys = (() => {
        throw new Error('cannot_render_api_keys_disabled')
      }) as typeof clerkMock.APIKeys

      const warnSpy = vi.spyOn(console, 'warn').mockImplementation(() => {})
      const errorSpy = vi.spyOn(console, 'error').mockImplementation(() => {})

      render(<ConnectView />)

      expect(screen.getByRole('alert')).toBeInTheDocument()
      expect(screen.getByText(/api keys are not enabled/i)).toBeInTheDocument()
      expect(screen.getByText(/clerk dashboard/i)).toBeInTheDocument()

      // Restore original mock
      vi.mocked(clerkMock).APIKeys = originalAPIKeys
      warnSpy.mockRestore()
      errorSpy.mockRestore()
    })
  })

  describe('API key tip banner', () => {
    it('tip is visible on initial render', () => {
      render(<ConnectView />)
      expect(screen.getByText(/when you create an api key, copy it immediately/i)).toBeInTheDocument()
    })

    it('tip text mentions losing the key and generating a new one', () => {
      render(<ConnectView />)
      expect(screen.getByText(/generate a new one/i)).toBeInTheDocument()
    })

    it('tip is dismissable via close button', async () => {
      const user = userEvent.setup()
      render(<ConnectView />)

      expect(screen.getByText(/when you create an api key, copy it immediately/i)).toBeInTheDocument()

      const dismissBtn = screen.getByRole('button', { name: /dismiss warning/i })
      await user.click(dismissBtn)

      expect(screen.queryByText(/when you create an api key, copy it immediately/i)).not.toBeInTheDocument()
    })
  })

  describe('tab navigation — T018/T020', () => {
    it('renders 4 tab buttons for AI coding assistants', () => {
      render(<ConnectView />)
      const tabs = screen.getAllByRole('tab')
      expect(tabs).toHaveLength(4)
    })

    it('default active tab is Claude Code (aria-selected=true)', () => {
      render(<ConnectView />)
      const claudeTab = screen.getByRole('tab', { name: /claude code/i })
      expect(claudeTab).toHaveAttribute('aria-selected', 'true')
    })

    it('inactive tabs have aria-selected=false', () => {
      render(<ConnectView />)
      for (const name of ['Cursor', 'GitHub Copilot', 'Amazon Kiro']) {
        expect(screen.getByRole('tab', { name: new RegExp(name, 'i') })).toHaveAttribute(
          'aria-selected',
          'false',
        )
      }
    })

    it('clicking Cursor tab shows Cursor config snippet and file path', async () => {
      const user = userEvent.setup()
      render(<ConnectView />)

      await user.click(screen.getByRole('tab', { name: /cursor/i }))

      // File path appears in both the label span and the description — at least one is present
      expect(screen.getAllByText(/\.cursor\/mcp\.json/i).length).toBeGreaterThanOrEqual(1)
      expect(screen.getByText(/YOUR_API_KEY/)).toBeInTheDocument()
    })

    it('clicking GitHub Copilot tab shows GitHub Copilot config snippet and file path', async () => {
      const user = userEvent.setup()
      render(<ConnectView />)

      await user.click(screen.getByRole('tab', { name: /github copilot/i }))

      expect(screen.getAllByText(/\.vscode\/mcp\.json/i).length).toBeGreaterThanOrEqual(1)
      expect(screen.getByText(/YOUR_API_KEY/)).toBeInTheDocument()
    })

    it('clicking Amazon Kiro tab shows Amazon Kiro config snippet and file path', async () => {
      const user = userEvent.setup()
      render(<ConnectView />)

      await user.click(screen.getByRole('tab', { name: /amazon kiro/i }))

      expect(screen.getAllByText(/\.kiro\/settings\/mcp\.json/i).length).toBeGreaterThanOrEqual(1)
      expect(screen.getByText(/YOUR_API_KEY/)).toBeInTheDocument()
    })

    it('clicked tab becomes active (aria-selected=true)', async () => {
      const user = userEvent.setup()
      render(<ConnectView />)

      await user.click(screen.getByRole('tab', { name: /cursor/i }))

      expect(screen.getByRole('tab', { name: /cursor/i })).toHaveAttribute(
        'aria-selected',
        'true',
      )
      expect(screen.getByRole('tab', { name: /claude code/i })).toHaveAttribute(
        'aria-selected',
        'false',
      )
    })
  })

  describe('copy buttons — T014/T015 (User Story 2)', () => {
    // Spy on clipboard.writeText for all copy-button tests
    beforeEach(() => {
      vi.spyOn(navigator.clipboard, 'writeText').mockResolvedValue(undefined)
    })

    afterEach(() => {
      vi.restoreAllMocks()
    })

    it('each assistant tab has a copy button', async () => {
      const user = userEvent.setup()
      render(<ConnectView />)

      for (const name of ['Claude Code', 'Cursor', 'GitHub Copilot', 'Amazon Kiro']) {
        await user.click(screen.getByRole('tab', { name: new RegExp(name, 'i') }))
        expect(
          screen.getByRole('button', { name: new RegExp(`copy ${name} config`, 'i') }),
        ).toBeInTheDocument()
      }
    })

    it('copy button for Claude Code has accessible label', () => {
      render(<ConnectView />)
      expect(screen.getByRole('button', { name: /copy claude code config/i })).toBeInTheDocument()
    })

    it('copy button for Cursor has accessible label', async () => {
      const user = userEvent.setup()
      render(<ConnectView />)
      await user.click(screen.getByRole('tab', { name: /cursor/i }))
      expect(screen.getByRole('button', { name: /copy cursor config/i })).toBeInTheDocument()
    })

    it('copy button for GitHub Copilot has accessible label', async () => {
      const user = userEvent.setup()
      render(<ConnectView />)
      await user.click(screen.getByRole('tab', { name: /github copilot/i }))
      expect(
        screen.getByRole('button', { name: /copy github copilot config/i }),
      ).toBeInTheDocument()
    })

    it('copy button for Amazon Kiro has accessible label', async () => {
      const user = userEvent.setup()
      render(<ConnectView />)
      await user.click(screen.getByRole('tab', { name: /amazon kiro/i }))
      expect(screen.getByRole('button', { name: /copy amazon kiro config/i })).toBeInTheDocument()
    })

    it('clicking copy button calls clipboard.writeText with the snippet text', async () => {
      const user = userEvent.setup()
      render(<ConnectView />)

      await user.click(screen.getByRole('button', { name: /copy claude code config/i }))

      // navigator.clipboard.writeText was set in beforeEach
      expect(navigator.clipboard.writeText).toHaveBeenCalledOnce()
      expect(navigator.clipboard.writeText).toHaveBeenCalledWith(
        expect.stringContaining('YOUR_API_KEY'),
      )
    })

    it('copy button uses pasted API key, not placeholder', async () => {
      const user = userEvent.setup()
      render(<ConnectView />)

      // Paste a real API key into the input
      const input = screen.getByRole('textbox', { name: /api key/i })
      await user.clear(input)
      await user.type(input, 'ak_live_realkey99')

      await user.click(screen.getByRole('button', { name: /copy claude code config/i }))

      expect(navigator.clipboard.writeText).toHaveBeenCalledWith(
        expect.stringContaining('ak_live_realkey99'),
      )
      expect(navigator.clipboard.writeText).not.toHaveBeenCalledWith(
        expect.stringContaining('YOUR_API_KEY'),
      )
    })

    it('copy button shows "Copied!" feedback after click', async () => {
      const user = userEvent.setup()
      render(<ConnectView />)

      const copyBtn = screen.getByRole('button', { name: /copy claude code config/i })
      expect(copyBtn).toHaveTextContent('Copy')

      await user.click(copyBtn)

      expect(copyBtn).toHaveTextContent('Copied!')
    })
  })

  describe('config snippets content', () => {
    it('renders a snippet for Claude Code CLI', () => {
      render(<ConnectView />)
      expect(screen.getByText(/claude mcp add/i)).toBeInTheDocument()
    })

    it('renders a snippet for Cursor', async () => {
      const user = userEvent.setup()
      render(<ConnectView />)
      await user.click(screen.getByRole('tab', { name: /cursor/i }))
      expect(screen.getAllByText(/\.cursor\/mcp\.json/i).length).toBeGreaterThanOrEqual(1)
    })

    it('renders a snippet for GitHub Copilot', async () => {
      const user = userEvent.setup()
      render(<ConnectView />)
      await user.click(screen.getByRole('tab', { name: /github copilot/i }))
      expect(screen.getAllByText(/\.vscode\/mcp\.json/i).length).toBeGreaterThanOrEqual(1)
    })

    it('renders a snippet for Amazon Kiro', async () => {
      const user = userEvent.setup()
      render(<ConnectView />)
      await user.click(screen.getByRole('tab', { name: /amazon kiro/i }))
      expect(screen.getAllByText(/\.kiro\/settings\/mcp\.json/i).length).toBeGreaterThanOrEqual(1)
    })
  })
})

describe('Navigation regression — FR-012', () => {
  it('Resumes tab button still renders', () => {
    render(<Navigation activeView="resumes" onNavigate={vi.fn()} />)
    expect(screen.getByRole('button', { name: /resumes/i })).toBeInTheDocument()
  })

  it('Applications tab button still renders', () => {
    render(<Navigation activeView="applications" onNavigate={vi.fn()} />)
    expect(screen.getByRole('button', { name: /applications/i })).toBeInTheDocument()
  })

  it('Accomplishments tab button still renders', () => {
    render(<Navigation activeView="accomplishments" onNavigate={vi.fn()} />)
    expect(screen.getByRole('button', { name: /accomplishments/i })).toBeInTheDocument()
  })

  it('Connect tab button renders after T011', () => {
    render(<Navigation activeView="connect" onNavigate={vi.fn()} />)
    expect(screen.getByRole('button', { name: /connect/i })).toBeInTheDocument()
  })

  it('Resumes tab button navigates to resumes view', async () => {
    const user = userEvent.setup()
    const onNavigate = vi.fn()
    render(<Navigation activeView="connect" onNavigate={onNavigate} />)

    await user.click(screen.getByRole('button', { name: /resumes/i }))
    expect(onNavigate).toHaveBeenCalledWith('resumes')
  })

  it('Applications tab button navigates to applications view', async () => {
    const user = userEvent.setup()
    const onNavigate = vi.fn()
    render(<Navigation activeView="connect" onNavigate={onNavigate} />)

    await user.click(screen.getByRole('button', { name: /applications/i }))
    expect(onNavigate).toHaveBeenCalledWith('applications')
  })

  it('Accomplishments tab button navigates to accomplishments view', async () => {
    const user = userEvent.setup()
    const onNavigate = vi.fn()
    render(<Navigation activeView="connect" onNavigate={onNavigate} />)

    await user.click(screen.getByRole('button', { name: /accomplishments/i }))
    expect(onNavigate).toHaveBeenCalledWith('accomplishments')
  })
})
