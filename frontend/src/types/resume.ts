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
export interface ApiError {
  detail: string
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
  created_at: string
  updated_at: string
}

export interface ResumeVersionSummary {
  id: number
  label: string
  is_default: boolean
  app_count: number
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

export interface Communication {
  id: number
  app_id: number
  contact_id: number | null
  contact_name: string | null
  type: string
  direction: string
  subject: string
  body: string
  date: string
  status: string
  created_at: string
}
