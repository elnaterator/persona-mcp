import { useState } from 'react'
import { Link } from 'react-router'
import { useUser } from '@clerk/clerk-react'
import { ChevronDown, ChevronRight } from 'lucide-react'
import {
  useAccomplishmentList,
  useApplicationList,
  useContactList,
  useNoteList,
  useResumeList,
} from '../../hooks/queries'
import styles from './HomeView.module.css'

// ─── Connect section ──────────────────────────────────────────────────────────

const MCP_SERVER_URL =
  import.meta.env.VITE_MCP_SERVER_URL ?? 'https://your-persona-server.com/mcp'

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
    snippet: `claude mcp add --transport http persona ${MCP_SERVER_URL}`,
  },
  {
    id: 'cursor',
    name: 'Cursor',
    filePath: '.cursor/mcp.json',
    snippet: JSON.stringify(
      { mcpServers: { persona: { url: MCP_SERVER_URL } } },
      null,
      2,
    ),
  },
  {
    id: 'github-copilot',
    name: 'GitHub Copilot',
    filePath: '.vscode/mcp.json',
    snippet: JSON.stringify(
      { servers: { persona: { type: 'http', url: MCP_SERVER_URL } } },
      null,
      2,
    ),
  },
  {
    id: 'amazon-kiro',
    name: 'Amazon Kiro',
    filePath: '.kiro/settings/mcp.json',
    snippet: JSON.stringify(
      { mcpServers: { persona: { url: MCP_SERVER_URL } } },
      null,
      2,
    ),
  },
]

function ConnectSection() {
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
    <div className={styles.connect}>
      <div className={styles.connectStep}>
        <h3 className={styles.stepTitle}>Add to your assistant</h3>
        <p className={styles.stepHint}>
          Your assistant will open a browser window to sign in (OAuth). No API key to manage.
        </p>
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
  )
}

// ─── Stats ────────────────────────────────────────────────────────────────────

const TERMINAL_STATUSES = new Set(['Rejected', 'Withdrawn', 'Accepted'])

// ─── Home ─────────────────────────────────────────────────────────────────────

export default function HomeView() {
  const { user } = useUser()
  const firstName = user?.firstName ?? null

  const [connectOpen, setConnectOpen] = useState(false)

  const resumes = useResumeList()
  const applications = useApplicationList()
  const notes = useNoteList()
  const accomplishments = useAccomplishmentList()
  const contacts = useContactList()

  const ready =
    resumes.isSuccess &&
    applications.isSuccess &&
    notes.isSuccess &&
    accomplishments.isSuccess &&
    contacts.isSuccess

  const stats = ready
    ? {
        resumes: resumes.data.length,
        applications: applications.data.length,
        activeApplications: applications.data.filter(
          (a) => !TERMINAL_STATUSES.has(a.status),
        ).length,
        notes: notes.data.length,
        accomplishments: accomplishments.data.length,
        contacts: contacts.data.length,
      }
    : null

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

        <Link to="/contacts" className={styles.statCard}>
          <span className={styles.statLabel}>Contacts</span>
          <span className={styles.statValue}>{stats === null ? '—' : stats.contacts}</span>
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
