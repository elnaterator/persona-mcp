import { Component, useEffect, useState } from 'react'
import type { ErrorInfo, ReactNode } from 'react'
import { Link } from 'react-router'
import { useUser } from '@clerk/clerk-react'
import { APIKeys } from '@clerk/clerk-react'
import { ChevronDown, ChevronRight } from 'lucide-react'
import { listResumes, listApplications, listNotes, listAccomplishments } from '../../services/api'
import styles from './HomeView.module.css'

// ─── Connect section ──────────────────────────────────────────────────────────

class APIKeysErrorBoundary extends Component<
  { children: ReactNode },
  { hasError: boolean }
> {
  constructor(props: { children: ReactNode }) {
    super(props)
    this.state = { hasError: false }
  }
  static getDerivedStateFromError() {
    return { hasError: true }
  }
  componentDidCatch(error: Error, info: ErrorInfo) {
    console.warn('APIKeys component error:', error.message, info.componentStack)
  }
  render() {
    if (this.state.hasError) {
      return (
        <div className={styles.apiKeysDisabled} role="alert">
          <strong>API keys are not enabled.</strong> Enable native API keys in your{' '}
          <a href="https://dashboard.clerk.com" target="_blank" rel="noopener noreferrer">
            Clerk Dashboard
          </a>{' '}
          under <em>Configure &rarr; API Keys</em>, then refresh.
        </div>
      )
    }
    return this.props.children
  }
}

const MCP_SERVER_URL =
  import.meta.env.VITE_MCP_SERVER_URL ?? 'https://your-persona-server.com/mcp'

const KEY_PLACEHOLDER = 'YOUR_API_KEY'

interface Assistant {
  id: string
  name: string
  filePath: string | null
  snippet: (key: string) => string
}

const ASSISTANTS: Assistant[] = [
  {
    id: 'claude-code',
    name: 'Claude Code',
    filePath: null,
    snippet: (key) =>
      `claude mcp add --transport http persona ${MCP_SERVER_URL} \\\n  --header "Authorization: Bearer ${key}"`,
  },
  {
    id: 'cursor',
    name: 'Cursor',
    filePath: '.cursor/mcp.json',
    snippet: (key) =>
      JSON.stringify(
        { mcpServers: { persona: { url: MCP_SERVER_URL, headers: { Authorization: `Bearer ${key}` } } } },
        null,
        2,
      ),
  },
  {
    id: 'github-copilot',
    name: 'GitHub Copilot',
    filePath: '.vscode/mcp.json',
    snippet: (key) =>
      JSON.stringify(
        { servers: { persona: { type: 'http', url: MCP_SERVER_URL, headers: { Authorization: `Bearer ${key}` } } } },
        null,
        2,
      ),
  },
  {
    id: 'amazon-kiro',
    name: 'Amazon Kiro',
    filePath: '.kiro/settings/mcp.json',
    snippet: (key) =>
      JSON.stringify(
        { mcpServers: { persona: { url: MCP_SERVER_URL, headers: { Authorization: `Bearer ${key}` } } } },
        null,
        2,
      ),
  },
]

function ConnectSection() {
  const [apiKey, setApiKey] = useState('')
  const [copiedId, setCopiedId] = useState<string | null>(null)
  const [activeTab, setActiveTab] = useState(ASSISTANTS[0].id)

  const displayKey = apiKey.trim() !== '' ? apiKey.trim() : KEY_PLACEHOLDER
  const activeAssistant = ASSISTANTS.find((a) => a.id === activeTab) ?? ASSISTANTS[0]
  const activeSnippet = activeAssistant.snippet(displayKey)

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
    <div className={styles.connect}>
      <div className={styles.connectStep}>
        <span className={styles.stepNumber}>01</span>
        <h3 className={styles.stepTitle}>Generate an API key</h3>
        <p className={styles.stepHint}>Copy it immediately — you will only see it once.</p>
        <APIKeysErrorBoundary>
          <APIKeys
            appearance={{
              variables: {
                colorBackground: '#1e1e1e',
                colorForeground: '#e0e0e0',
                colorInput: '#111111',
                colorInputForeground: '#e0e0e0',
                colorMutedForeground: '#888888',
                colorNeutral: '#aaaaaa',
                colorPrimary: '#52b788',
                colorDanger: '#ff4444',
                fontFamily: "'JetBrains Mono', 'Fira Code', 'SF Mono', ui-monospace, monospace",
                borderRadius: '0px',
              },
              elements: {
                tableHead: { color: '#555555' },
                tableCell: { color: '#e0e0e0' },
                menuButton: { color: '#aaaaaa' },
                menuItem: { color: '#e0e0e0', backgroundColor: '#1e1e1e' },
                selectButton: { backgroundColor: '#111111', color: '#e0e0e0' },
                selectOption: { backgroundColor: '#1e1e1e', color: '#e0e0e0' },
              },
            }}
          />
        </APIKeysErrorBoundary>
      </div>

      <div className={styles.connectStep}>
        <span className={styles.stepNumber}>02</span>
        <h3 className={styles.stepTitle}>Paste your key</h3>
        <div className={styles.pasteRow}>
          <input
            type="text"
            className={styles.pasteInput}
            placeholder="Paste your API key here (ak_...)"
            value={apiKey}
            onChange={(e) => setApiKey(e.target.value)}
            aria-label="Paste API key"
            spellCheck={false}
            autoComplete="off"
          />
          <span className={styles.pasteHint}>Stored only in this browser tab.</span>
        </div>
      </div>

      <div className={styles.connectStep}>
        <span className={styles.stepNumber}>03</span>
        <h3 className={styles.stepTitle}>Add to your assistant</h3>
        <div className={styles.tabList} role="tablist" aria-label="AI coding assistants">
          {ASSISTANTS.map((a) => (
            <button
              key={a.id}
              role="tab"
              aria-selected={activeTab === a.id}
              className={`${styles.tab} ${activeTab === a.id ? styles.tabActive : ''}`}
              onClick={() => setActiveTab(a.id)}
            >
              {a.name}
            </button>
          ))}
        </div>
        <div className={styles.tabPanel} role="tabpanel">
          {activeAssistant.filePath && (
            <span className={styles.filePath}>{activeAssistant.filePath}</span>
          )}
          <div className={styles.snippetRow}>
            <pre className={styles.codeBlock}>{activeSnippet}</pre>
            <button
              className={`${styles.copyBtn} ${copiedId === activeAssistant.id ? styles.copyBtnDone : ''}`}
              aria-label={`Copy ${activeAssistant.name} config`}
              onClick={() => handleCopy(activeAssistant.id, activeSnippet)}
            >
              {copiedId === activeAssistant.id ? 'Copied!' : 'Copy'}
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

// ─── Stats ────────────────────────────────────────────────────────────────────

const TERMINAL_STATUSES = new Set(['Rejected', 'Withdrawn', 'Accepted'])

interface Stats {
  resumes: number
  applications: number
  activeApplications: number
  notes: number
  accomplishments: number
}

// ─── Home ─────────────────────────────────────────────────────────────────────

export default function HomeView() {
  const { user } = useUser()
  const firstName = user?.firstName ?? null

  const [stats, setStats] = useState<Stats | null>(null)
  const [connectOpen, setConnectOpen] = useState(false)

  useEffect(() => {
    Promise.all([listResumes(), listApplications(), listNotes(), listAccomplishments()]).then(
      ([resumes, applications, notes, accomplishments]) => {
        const active = applications.filter((a) => !TERMINAL_STATUSES.has(a.status))
        setStats({
          resumes: (resumes || []).length,
          applications: (applications || []).length,
          activeApplications: active.length,
          notes: (notes || []).length,
          accomplishments: (accomplishments || []).length,
        })
      }
    )
  }, [])

  return (
    <div className={styles.container}>
      <h2 className={styles.heading}>
        {firstName ? `Hey, ${firstName}.` : 'Overview'}
      </h2>

      <div className={styles.statsGrid}>
        <Link to="/resumes" className={styles.statCard}>
          <span className={styles.statLabel}>Resumes</span>
          <span className={styles.statValue}>{stats === null ? '—' : stats.resumes}</span>
        </Link>

        <Link to="/applications" className={styles.statCard}>
          <span className={styles.statLabel}>Applications</span>
          <span className={styles.statValue}>{stats === null ? '—' : stats.applications}</span>
          {stats !== null && stats.activeApplications > 0 && (
            <span className={styles.statSub}>{stats.activeApplications} active</span>
          )}
        </Link>

        <Link to="/accomplishments" className={styles.statCard}>
          <span className={styles.statLabel}>Accomplishments</span>
          <span className={styles.statValue}>{stats === null ? '—' : stats.accomplishments}</span>
        </Link>

        <Link to="/notes" className={styles.statCard}>
          <span className={styles.statLabel}>Notes</span>
          <span className={styles.statValue}>{stats === null ? '—' : stats.notes}</span>
        </Link>
      </div>

      <div className={styles.connectSection}>
        <button
          className={styles.connectToggle}
          onClick={() => setConnectOpen((o) => !o)}
          aria-expanded={connectOpen}
        >
          {connectOpen ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
          Connect your AI assistant
        </button>
        {connectOpen && <ConnectSection />}
      </div>
    </div>
  )
}
