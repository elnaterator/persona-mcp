/**
 * TypeScript type definitions for notes.
 */

import type { GroupedLinks } from './link'

export interface Note {
  id: number
  title: string
  content: string
  tags: string[]
  created_at: string
  updated_at: string
  links: GroupedLinks
}

export interface NoteSummary {
  id: number
  title: string
  tags: string[]
  created_at: string
  updated_at: string
  link_count?: number
}
