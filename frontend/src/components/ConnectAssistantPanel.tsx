import { useState } from 'react'
import { Bot, ChevronLeft, ChevronRight } from 'lucide-react'
import styles from './ConnectAssistantPanel.module.css'

// The SPA is served same-origin as the `/mcp` endpoint, so derive the URL from
// the current page origin at runtime — correct for localhost, dev, and prod
// without a per-environment rebuild. `VITE_MCP_SERVER_URL` stays an explicit
// override for `vite dev`, where the SPA (:5173) and backend (:8000) differ.
const MCP_SERVER_URL =
  import.meta.env.VITE_MCP_SERVER_URL ??
  (typeof window !== 'undefined'
    ? `${window.location.origin}/mcp`
    : 'https://your-pktx-server.com/mcp')

interface Assistant {
  id: string
  name: string
  filePath: string | null
  snippet: string
}

const ASSISTANTS: Assistant[] = [
  {
    id: 'claude-code',
    name: 'Claude Code',
    filePath: null,
    snippet: `claude mcp add --transport http pktx ${MCP_SERVER_URL}`,
  },
  {
    id: 'cursor',
    name: 'Cursor',
    filePath: '.cursor/mcp.json',
    snippet: JSON.stringify(
      { mcpServers: { pktx: { url: MCP_SERVER_URL } } },
      null,
      2,
    ),
  },
  {
    id: 'github-copilot',
    name: 'GitHub Copilot',
    filePath: '.vscode/mcp.json',
    snippet: JSON.stringify(
      { servers: { pktx: { type: 'http', url: MCP_SERVER_URL } } },
      null,
      2,
    ),
  },
  {
    id: 'amazon-kiro',
    name: 'Amazon Kiro',
    filePath: '.kiro/settings/mcp.json',
    snippet: JSON.stringify(
      { mcpServers: { pktx: { url: MCP_SERVER_URL } } },
      null,
      2,
    ),
  },
  {
    id: 'claude-desktop',
    name: 'Claude Desktop',
    filePath: 'Settings → Connectors → Add custom connector',
    snippet: MCP_SERVER_URL,
  },
  {
    id: 'windsurf',
    name: 'Windsurf',
    filePath: '~/.codeium/windsurf/mcp_config.json',
    snippet: JSON.stringify(
      { mcpServers: { pktx: { serverUrl: MCP_SERVER_URL } } },
      null,
      2,
    ),
  },
  {
    id: 'zed',
    name: 'Zed',
    filePath: '~/.config/zed/settings.json',
    snippet: JSON.stringify(
      { context_servers: { pktx: { url: MCP_SERVER_URL } } },
      null,
      2,
    ),
  },
  {
    id: 'cline',
    name: 'Cline',
    filePath: 'cline_mcp_settings.json (via "Configure MCP Servers")',
    snippet: JSON.stringify(
      { mcpServers: { pktx: { type: 'streamableHttp', url: MCP_SERVER_URL } } },
      null,
      2,
    ),
  },
]

export default function ConnectAssistantPanel() {
  const [open, setOpen] = useState(false)
  const [copiedId, setCopiedId] = useState<string | null>(null)
  const [activeTab, setActiveTab] = useState(ASSISTANTS[0].id)

  const activeAssistant = ASSISTANTS.find((a) => a.id === activeTab) ?? ASSISTANTS[0]

  const handleCopy = async (assistantId: string, text: string) => {
    try {
      await navigator.clipboard.writeText(text)
      setCopiedId(assistantId)
      setTimeout(() => setCopiedId(null), 2000)
    } catch {
      // Clipboard access denied
    }
  }

  return (
    <aside className={`${styles.panel} ${open ? styles.panelOpen : styles.panelClosed}`}>
      {open ? (
        <div className={styles.content}>
          <button
            className={styles.collapseBtn}
            onClick={() => setOpen(false)}
            aria-expanded={true}
            aria-label="Collapse AI assistant panel"
          >
            <Bot size={20} />
            <span className={styles.collapseLabel}>Connect your AI assistant</span>
            <ChevronLeft size={16} />
          </button>

          <div className={styles.body}>
            <h3 className={styles.stepTitle}>Add to your assistant</h3>
            <p className={styles.stepHint}>
              Your assistant will open a browser window to sign in (OAuth). No API key to manage.
            </p>
            <label className={styles.selectLabel} htmlFor="assistant-select">
              Assistant
            </label>
            <select
              id="assistant-select"
              className={styles.select}
              value={activeTab}
              onChange={(e) => setActiveTab(e.target.value)}
            >
              {ASSISTANTS.map((a) => (
                <option key={a.id} value={a.id}>
                  {a.name}
                </option>
              ))}
            </select>
            <div className={styles.tabPanel}>
              {activeAssistant.filePath && (
                <span className={styles.filePath}>{activeAssistant.filePath}</span>
              )}
              <div className={styles.snippetRow}>
                <pre className={styles.codeBlock}>{activeAssistant.snippet}</pre>
                <button
                  className={`${styles.copyBtn} ${copiedId === activeAssistant.id ? styles.copyBtnDone : ''}`}
                  aria-label={`Copy ${activeAssistant.name} config`}
                  onClick={() => handleCopy(activeAssistant.id, activeAssistant.snippet)}
                >
                  {copiedId === activeAssistant.id ? 'Copied!' : 'Copy'}
                </button>
              </div>
            </div>
          </div>
        </div>
      ) : (
        <button
          className={styles.expandBtn}
          onClick={() => setOpen(true)}
          aria-expanded={false}
          aria-label="Connect your AI assistant"
        >
          <Bot size={28} />
          <span className={styles.expandLabel}>Connect</span>
          <ChevronRight size={18} />
        </button>
      )}
    </aside>
  )
}
