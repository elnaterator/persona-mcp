import { useState } from 'react'
import { Link } from 'react-router'
import { Link2 } from 'lucide-react'
import {
  useAccomplishmentList,
  useAccomplishmentMutations,
  useAllTags,
} from '../../hooks/queries'
import { TagInput } from '../../components/TagInput'
import { useToast } from '../../components/toast'
import { AccomplishmentPanel } from './AccomplishmentPanel'
import type { AccomplishmentCreateInput } from '../../schemas/accomplishment'
import styles from './AccomplishmentListView.module.css'

export default function AccomplishmentListView() {
  const [tagFilter, setTagFilter] = useState<string[]>([])
  const [showForm, setShowForm] = useState(false)

  const listQuery = useAccomplishmentList({ tags: tagFilter })
  const tagsQuery = useAllTags()
  const { create } = useAccomplishmentMutations()
  const { success, error } = useToast()

  const accomplishments = listQuery.data ?? []
  const allTags = tagsQuery.data ?? []

  const handleCreate = async (data: AccomplishmentCreateInput) => {
    try {
      await create.mutateAsync({
        title: data.title,
        situation: data.situation ?? undefined,
        task: data.task ?? undefined,
        action: data.action ?? undefined,
        result: data.result ?? undefined,
        accomplishment_date: data.accomplishment_date ?? null,
        tags: data.tags ?? [],
      })
      setShowForm(false)
      success('Accomplishment created')
    } catch (err) {
      error(err instanceof Error ? err.message : 'Failed to create accomplishment')
      throw err
    }
  }

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <h2 className={styles.heading}>Accomplishments</h2>
        <button
          className={styles.newButton}
          onClick={() => setShowForm((v) => !v)}
        >
          {showForm ? 'Cancel' : 'New Accomplishment'}
        </button>
      </div>

      {showForm && (
        <AccomplishmentPanel
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
      </div>

      {accomplishments.length === 0 ? (
        <p className={styles.empty}>No accomplishments yet. Click &quot;New Accomplishment&quot; to add one.</p>
      ) : (
        <ul className={styles.list}>
          {accomplishments.map((acc) => (
            <li key={acc.id} className={styles.item}>
              <Link to={`/accomplishments/${acc.id}`} className={styles.itemLink}>
                <div className={styles.itemTitle}>{acc.title}</div>
                <div className={styles.itemMeta}>
                  {acc.accomplishment_date && (
                    <span>{acc.accomplishment_date}</span>
                  )}
                  {!!acc.link_count && (
                    <span className={styles.linkCount}><Link2 size={11} />{acc.link_count}</span>
                  )}
                </div>
                {acc.tags.length > 0 && (
                  <div className={styles.itemTags}>
                    {acc.tags.map((tag) => (
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
