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
  /** Extra setup detail, shown under the snippet. Only for assistants that need it. */
  notes?: string[]
}

const ASSISTANTS: Assistant[] = [
  {
    id: 'claude-desktop',
    name: 'Claude Desktop',
    filePath: 'Settings → Connectors → Add custom connector',
    snippet: MCP_SERVER_URL,
  },
  {
    id: 'chatgpt',
    name: 'ChatGPT',
    filePath:
      'chatgpt.com → Settings → Apps → Advanced settings → turn on Developer mode, then Plugins → Create → paste the URL below and pick OAuth (set this up on the web; the desktop app picks it up afterwards)',
    snippet: MCP_SERVER_URL,
    notes: [
      'Developer mode is web-only and needs a Plus, Pro, Business, Enterprise, or Education plan. On Business/Enterprise an admin enables it first under Workspace Settings → Permissions & Roles.',
      'Give it a name and a description — ChatGPT reads the description when deciding whether to use pktx.',
      'Older builds label the section Connectors instead of Plugins; the steps are the same.',
    ],
  },
  {
    id: 'claude-code',
    name: 'Claude Code',
    filePath: null,
    snippet: `claude mcp add --transport http pktx ${MCP_SERVER_URL}`,
  },
  {
    id: 'grok-build',
    name: 'Grok Build',
    filePath: null,
    snippet: `grok mcp add --transport http pktx ${MCP_SERVER_URL}`,
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
              {activeAssistant.notes && (
                <ul className={styles.notes}>
                  {activeAssistant.notes.map((note) => (
                    <li key={note}>{note}</li>
                  ))}
                </ul>
              )}
            </div>

            <div className={styles.about}>
              <h4 className={styles.aboutTitle}>What is this?</h4>
              <p className={styles.aboutText}>
                This connects your AI assistant directly to your pktx data — your resumes,
                applications, accomplishments, notes, and contacts — so you can ask it questions
                and give it tasks instead of copying and pasting information back and forth.
              </p>
              <div className={styles.callout}>
                Your assistant can both <strong>read and write</strong> your data — it can look
                things up, but it can also log a new application, add an accomplishment, or update
                a note on its own when you ask it to.
              </div>
              <ol className={styles.aboutSteps}>
                <li>Pick your assistant above and follow its step.</li>
                <li>When it opens a browser window, sign in — that's the one-time OAuth step.</li>
                <li>
                  Test it: ask your assistant something like &ldquo;list my resumes&rdquo; or
                  &ldquo;what applications do I have open?&rdquo;. If it answers with your real
                  data, you're connected.
                </li>
              </ol>
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
