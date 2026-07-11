import { useRef, useState } from 'react'
import { Link } from 'react-router'
import { useUser } from '@clerk/clerk-react'
import { ChevronDown, ChevronRight } from 'lucide-react'
import {
  useAccomplishmentList,
  useApplicationList,
  useContactList,
  useGlobalSearch,
  useNoteList,
  useResumeList,
  useAllTags,
} from '../../hooks/queries'
import { SearchBar } from '../../components/SearchBar'
import type { SearchResult, SearchValue } from '../../types'
import styles from './HomeView.module.css'

// ─── Connect section ──────────────────────────────────────────────────────────

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

// ─── Search results ────────────────────────────────────────────────────────────

const TYPE_ORDER = ['resume', 'application', 'accomplishment', 'note', 'contact', 'communication']
const TYPE_LABELS: Record<string, string> = {
  resume: 'Resumes',
  application: 'Applications',
  accomplishment: 'Accomplishments',
  note: 'Notes',
  contact: 'Contacts',
  communication: 'Communications',
}

function SearchResults({ results, loading }: { results: SearchResult[]; loading: boolean }) {
  if (loading) {
    return <p className={styles.searchHint}>Searching...</p>
  }

  if (results.length === 0) {
    return <p className={styles.searchHint}>No results.</p>
  }

  const grouped = new Map<string, SearchResult[]>()
  for (const r of results) {
    if (!grouped.has(r.type)) grouped.set(r.type, [])
    grouped.get(r.type)!.push(r)
  }

  const orderedTypes = TYPE_ORDER.filter((t) => grouped.has(t))

  return (
    <div className={styles.searchResults}>
      {orderedTypes.map((type) => {
        const items = grouped.get(type)!
        return (
          <div key={type} className={styles.searchGroup}>
            <div className={styles.searchGroupHeader}>
              {TYPE_LABELS[type] ?? type} <span className={styles.searchGroupCount}>{items.length}</span>
            </div>
            <ul className={styles.searchResultList}>
              {items.map((item) => (
                <li key={`${item.type}-${item.id}`}>
                  <Link to={item.url} className={styles.searchResultRow}>
                    <span className={styles.searchResultTitle}>{item.title}</span>
                    {item.subtitle && (
                      <span className={styles.searchResultSub}>{item.subtitle}</span>
                    )}
                    {item.snippet && (
                      <span className={styles.searchResultSnippet}>{item.snippet}</span>
                    )}
                  </Link>
                </li>
              ))}
            </ul>
          </div>
        )
      })}
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
  const [searchValue, setSearchValue] = useState<SearchValue>({ tags: [], text: '' })
  const [debouncedSearch, setDebouncedSearch] = useState<SearchValue>({ tags: [], text: '' })
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  const tagsQuery = useAllTags()
  const allTags = tagsQuery.data ?? []

  const hasSearch = debouncedSearch.text.length > 0 || debouncedSearch.tags.length > 0
  const searchQuery = useGlobalSearch({
    q: debouncedSearch.text || undefined,
    tags: debouncedSearch.tags.length > 0 ? debouncedSearch.tags : undefined,
    enabled: hasSearch,
  })

  const handleSearchChange = (v: SearchValue) => {
    setSearchValue(v)
    if (debounceRef.current) clearTimeout(debounceRef.current)
    debounceRef.current = setTimeout(() => setDebouncedSearch(v), 300)
  }

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

      <div className={styles.globalSearch}>
        <SearchBar
          value={searchValue}
          onChange={handleSearchChange}
          availableTags={allTags}
          placeholder="Search everything..."
        />
        {hasSearch && (
          <SearchResults
            results={searchQuery.data ?? []}
            loading={searchQuery.isFetching}
          />
        )}
        {!hasSearch && (
          <p className={styles.searchHint}>Type to search across all resources.</p>
        )}
      </div>

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
