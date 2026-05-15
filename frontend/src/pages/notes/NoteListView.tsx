import { useState } from 'react'
import { Link } from 'react-router'
import { Link2 } from 'lucide-react'
import { useAllTags, useNoteList, useNoteMutations } from '../../hooks/queries'
import { TagInput } from '../../components/TagInput'
import { useToast } from '../../components/toast'
import { NotePanel } from './NotePanel'
import type { NoteCreateInput } from '../../schemas/note'
import styles from './NoteListView.module.css'

export default function NoteListView() {
  const [tagFilter, setTagFilter] = useState<string[]>([])
  const [searchQuery, setSearchQuery] = useState('')
  const [showForm, setShowForm] = useState(false)

  const listQuery = useNoteList({ tags: tagFilter, q: searchQuery })
  const tagsQuery = useAllTags()
  const { create } = useNoteMutations()
  const { success, error } = useToast()

  const notes = listQuery.data ?? []
  const allTags = tagsQuery.data ?? []

  const handleCreate = async (data: NoteCreateInput) => {
    try {
      await create.mutateAsync({
        title: data.title,
        content: data.content ?? undefined,
        tags: data.tags ?? [],
      })
      setShowForm(false)
      success('Note created')
    } catch (err) {
      error(err instanceof Error ? err.message : 'Failed to create note')
      throw err
    }
  }

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <h2 className={styles.heading}>Notes</h2>
        <button
          className={styles.newButton}
          onClick={() => setShowForm((v) => !v)}
        >
          {showForm ? 'Cancel' : 'New Note'}
        </button>
      </div>

      {showForm && (
        <NotePanel
          mode="create"
          allTags={allTags}
          onSave={handleCreate}
          onCancel={() => setShowForm(false)}
        />
      )}

      <div className={styles.filters}>
        <TagInput
          value={tagFilter}
          onChange={setTagFilter}
          availableTags={allTags}
          allowCreate={false}
          placeholder="Filter by tag..."
        />
        <input
          className={styles.searchInput}
          type="text"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          placeholder="Search notes..."
        />
      </div>

      {notes.length === 0 ? (
        <p className={styles.empty}>No notes yet. Click &quot;New Note&quot; to add one.</p>
      ) : (
        <ul className={styles.list}>
          {notes.map((note) => (
            <li key={note.id} className={styles.item}>
              <Link to={`/notes/${note.id}`} className={styles.itemLink}>
                <div className={styles.itemTitle}>{note.title}</div>
                <div className={styles.itemMeta}>
                  <span>{new Date(note.updated_at).toLocaleDateString()}</span>
                  {!!note.link_count && (
                    <span className={styles.linkCount}><Link2 size={11} />{note.link_count}</span>
                  )}
                </div>
                {note.tags.length > 0 && (
                  <div className={styles.itemTags}>
                    {note.tags.map((tag) => (
                      <span key={tag} className={styles.tagBadge}>
                        {tag}
                      </span>
                    ))}
                  </div>
                )}
              </Link>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
