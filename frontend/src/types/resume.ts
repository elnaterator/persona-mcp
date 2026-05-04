/**
 * TypeScript type definitions for resume data.
 *
 * These types mirror the backend Pydantic models exactly.
 * Field names use snake_case to match the JSON API responses.
 */

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

/**
 * API error response format
 */
export interface ApiValidationError {
  loc: string[]
  msg: string
  type: string
}

export interface ApiError {
  detail: string | ApiValidationError[]
}

/**
 * API success response format (for mutations)
 */
export interface ApiSuccessResponse {
  message: string
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
}

export interface ResumeVersionSummary {
  id: number
  label: string
  is_default: boolean
  app_count: number
  tags: string[]
  created_at: string
  updated_at: string
}

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
}

export interface AccomplishmentSummary {
  id: number
  title: string
  accomplishment_date: string | null
  tags: string[]
  created_at: string
  updated_at: string
}

export interface Note {
  id: number
  title: string
  content: string
  tags: string[]
  created_at: string
  updated_at: string
}

export interface NoteSummary {
  id: number
  title: string
  tags: string[]
  created_at: string
  updated_at: string
}

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
}

export interface Communication {
  id: number
  app_id?: number | null
  contact_ref_id?: number | null
  contact_id?: number | null
  contact_name?: string | null
  type: string
  direction: string
  subject: string
  body: string
  date: string
  status: string
  tags: string[]
  created_at: string
}

export interface CommunicationSearchResult extends Communication {
  parentType: 'application' | 'contact'
  parentId: number
  parentName: string
}
