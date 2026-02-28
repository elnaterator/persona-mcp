/**
 * ConnectView — Connect tab content component (011-mcp-instructions)
 *
 * Renders:
 * 1. Clerk <APIKeys /> component for key lifecycle (generate / revoke)
 * 2. Warning banner after key creation (shown once, dismissable)
 * 3. Paste-input field so users can substitute their key into config snippets
 * 4. Tabbed config snippet blocks for all 4 supported AI coding assistants (T018)
 *
 * T016 verification: The Clerk <APIKeys /> component includes a built-in
 * confirmation step before key revocation (standard Clerk UX pattern — all
 * destructive actions in Clerk's prebuilt components require explicit
 * confirmation). APIKeysProps exposes no `confirmRevoke` prop, meaning
 * revocation confirmation is handled entirely within the component's own UI.
 * Therefore, no additional `confirmingRegeneration` boolean state is required
 * in this component.
 */

import { useState } from 'react'
import { APIKeys } from '@clerk/clerk-react'
import styles from './ConnectView.module.css'

const MCP_SERVER_URL =
  import.meta.env.VITE_MCP_SERVER_URL ?? 'https://your-persona-server.com/mcp'

const KEY_PLACEHOLDER = 'YOUR_API_KEY'

interface Assistant {
  id: string
  name: string
  filePath: string | null
  description: string
  snippet: (key: string) => string
}

const ASSISTANTS: Assistant[] = [
  {
    id: 'claude-code',
    name: 'Claude Code',
    filePath: null,
    description: 'Add Persona as an MCP server in Claude Code using the CLI.',
    snippet: (key) =>
      `claude mcp add --transport http persona ${MCP_SERVER_URL} \\\n  --header "Authorization: Bearer ${key}"`,
  },
  {
    id: 'cursor',
    name: 'Cursor',
    filePath: '.cursor/mcp.json',
    description:
      'Add Persona as an MCP server in Cursor by editing .cursor/mcp.json in your project root.',
    snippet: (key) =>
      JSON.stringify(
        {
          mcpServers: {
            persona: {
              url: MCP_SERVER_URL,
              headers: { Authorization: `Bearer ${key}` },
            },
          },
        },
        null,
        2,
      ),
  },
  {
    id: 'github-copilot',
    name: 'GitHub Copilot',
    filePath: '.vscode/mcp.json',
    description:
      'Add Persona as an MCP server in GitHub Copilot (VS Code) by editing .vscode/mcp.json in your project root.',
    snippet: (key) =>
      JSON.stringify(
        {
          servers: {
            persona: {
              type: 'http',
              url: MCP_SERVER_URL,
              headers: { Authorization: `Bearer ${key}` },
            },
          },
        },
        null,
        2,
      ),
  },
  {
    id: 'amazon-kiro',
    name: 'Amazon Kiro',
    filePath: '.kiro/settings/mcp.json',
    description:
      'Add Persona as an MCP server in Amazon Kiro by editing .kiro/settings/mcp.json in your project root.',
    snippet: (key) =>
      JSON.stringify(
        {
          mcpServers: {
            persona: {
              url: MCP_SERVER_URL,
              headers: { Authorization: `Bearer ${key}` },
            },
          },
        },
        null,
        2,
      ),
  },
]

interface ConnectViewProps {
  /** Test-only prop: force keyJustCreated=true to test warning banner. */
  testKeyJustCreated?: boolean
}

export default function ConnectView({ testKeyJustCreated = false }: ConnectViewProps) {
  const [apiKey, setApiKey] = useState('')
  const [keyJustCreated, setKeyJustCreated] = useState(testKeyJustCreated)
  const [copiedId, setCopiedId] = useState<string | null>(null)
  const [activeTab, setActiveTab] = useState(ASSISTANTS[0].id)

  const displayKey = apiKey.trim() || KEY_PLACEHOLDER

  const handleCopy = async (assistantId: string, text: string) => {
    try {
      await navigator.clipboard.writeText(text)
      setCopiedId(assistantId)
      setTimeout(() => setCopiedId(null), 2000)
    } catch {
      // Clipboard access denied — silently ignore
    }
  }

  const activeAssistant = ASSISTANTS.find((a) => a.id === activeTab) ?? ASSISTANTS[0]
  const activeSnippet = activeAssistant.snippet(displayKey)

  return (
    <div className={styles.container}>
      <h2 className={styles.heading}>Connect an AI Coding Assistant</h2>
      <p className={styles.subheading}>
        Generate an API key, paste it below to populate config commands, then follow the
        setup instructions for your assistant.
      </p>

      {/* Warning banner — shown after key creation */}
      {keyJustCreated && (
        <div className={styles.warningBanner} role="alert">
          <span className={styles.warningIcon} aria-hidden="true">
            ⚠️
          </span>
          <p className={styles.warningText}>
            Copy your API key now — this is the only time you will see it in full. If you
            lose it, you will need to generate a new one.
          </p>
          <button
            className={styles.warningDismiss}
            aria-label="Dismiss"
            onClick={() => setKeyJustCreated(false)}
          >
            ✕
          </button>
        </div>
      )}

      <div className={styles.layout}>
        {/* Left: API key management */}
        <div className={styles.apiKeySection}>
          <h3 className={styles.sectionTitle}>Your API Key</h3>
          <APIKeys
            onKeyCreated={() => setKeyJustCreated(true)}
            onKeyRegenerated={() => setKeyJustCreated(true)}
          />

          {/* Paste-input field */}
          <div className={styles.pasteInputWrapper}>
            <label htmlFor="paste-api-key" className={styles.pasteLabel}>
              Paste your API key to populate config commands
            </label>
            <input
              id="paste-api-key"
              type="text"
              className={styles.pasteInput}
              placeholder="Paste your API key here (ak_...)"
              value={apiKey}
              onChange={(e) => setApiKey(e.target.value)}
              aria-label="Paste API key"
              spellCheck={false}
              autoComplete="off"
            />
            <span className={styles.pasteInputHint}>
              Your key is only stored locally in this browser tab — never sent to our
              servers.
            </span>
          </div>
        </div>

        {/* Right: Config snippets with tab navigation */}
        <div className={styles.snippetsSection}>
          <h3 className={styles.sectionTitle}>Config Commands</h3>
          <div className={styles.tabList} role="tablist" aria-label="AI coding assistants">
            {ASSISTANTS.map((assistant) => (
              <button
                key={assistant.id}
                role="tab"
                aria-selected={activeTab === assistant.id}
                className={`${styles.tab} ${activeTab === assistant.id ? styles.tabActive : ''}`}
                onClick={() => setActiveTab(assistant.id)}
              >
                {assistant.name}
              </button>
            ))}
          </div>
          <div className={styles.tabPanel} role="tabpanel">
            {activeAssistant.filePath && (
              <span className={styles.assistantFilePath}>{activeAssistant.filePath}</span>
            )}
            <p className={styles.assistantDescription}>{activeAssistant.description}</p>
            <div className={styles.snippetWrapper}>
              <pre className={styles.codeBlock}>{activeSnippet}</pre>
              <button
                className={`${styles.copyButton} ${copiedId === activeAssistant.id ? styles.copyButtonCopied : ''}`}
                aria-label={`Copy ${activeAssistant.name} config`}
                onClick={() => handleCopy(activeAssistant.id, activeSnippet)}
              >
                {copiedId === activeAssistant.id ? 'Copied!' : 'Copy'}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
