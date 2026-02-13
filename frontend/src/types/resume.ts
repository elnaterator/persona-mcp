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
