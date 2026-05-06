/**
 * TypeScript type definitions for accomplishments.
 */

import type { GroupedLinks } from './link'

export interface Accomplishment {
  id: number
  title: string
  situation: string
  task: string
  action: string
  result: string
  accomplishment_date: string | null
  tags: string[]
  created_at: string
  updated_at: string
  links: GroupedLinks
}

export interface AccomplishmentSummary {
  id: number
  title: string
  accomplishment_date: string | null
  tags: string[]
  created_at: string
  updated_at: string
  link_count?: number
}
