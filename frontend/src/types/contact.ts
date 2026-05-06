/**
 * TypeScript type definitions for networking contacts.
 */

import type { GroupedLinks } from './link'

export interface Contact {
  id: number
  name: string
  email?: string | null
  phone?: string | null
  company?: string | null
  title?: string | null
  relationship?: string | null
  linkedin_url?: string | null
  location?: string | null
  last_contacted_date?: string | null
  followup_date?: string | null
  notes: string
  tags: string[]
  created_at: string
  updated_at: string
  links: GroupedLinks
}

export interface ContactSummary {
  id: number
  name: string
  company?: string | null
  title?: string | null
  relationship?: string | null
  followup_date?: string | null
  tags: string[]
  updated_at: string
  link_count?: number
}
