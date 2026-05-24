/**
 * TypeScript type definitions for job applications.
 */

import type { GroupedLinks } from './link'

export interface Application {
  id: number
  company: string
  position: string
  description: string
  status: string
  url: string | null
  notes: string
  tags: string[]
  created_at: string
  updated_at: string
  links: GroupedLinks
  link_count?: number
}

export interface ApplicationSummary {
  id: number
  company: string
  position: string
  status: string
  url: string | null
  tags: string[]
  created_at: string
  updated_at: string
  link_count?: number
}
