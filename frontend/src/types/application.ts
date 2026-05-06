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
  resume_version_id: number | null
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
  resume_version_id: number | null
  tags: string[]
  created_at: string
  updated_at: string
  link_count?: number
}

export interface ApplicationContact {
  id: number
  app_id: number
  name: string
  role: string | null
  email: string | null
  phone: string | null
  notes: string
  created_at: string
}
