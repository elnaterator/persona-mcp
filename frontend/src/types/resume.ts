/**
 * TypeScript type definitions for resume data.
 *
 * These types mirror the backend Pydantic models exactly.
 * Field names use snake_case to match the JSON API responses.
 */

import type { GroupedLinks } from './link'

export interface ContactInfo {
  name: string | null
  email: string | null
  phone: string | null
  location: string | null
  linkedin: string | null
  website: string | null
  github: string | null
}

export interface WorkExperience {
  title: string
  company: string
  start_date: string | null
  end_date: string | null
  location: string | null
  highlights: string[]
}

export interface Education {
  institution: string
  degree: string
  field: string | null
  start_date: string | null
  end_date: string | null
  honors: string | null
  highlights: string[]
}

export interface Skill {
  name: string
  category: string | null
}

export interface Resume {
  contact: ContactInfo
  summary: string
  experience: WorkExperience[]
  education: Education[]
  skills: Skill[]
}

export interface ResumeVersion {
  id: number
  label: string
  is_default: boolean
  resume_data: Resume
  app_count: number
  tags: string[]
  created_at: string
  updated_at: string
  links: GroupedLinks
}

export interface ResumeVersionSummary {
  id: number
  label: string
  is_default: boolean
  app_count: number
  tags: string[]
  created_at: string
  updated_at: string
  link_count?: number
}
