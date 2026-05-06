/**
 * Barrel re-export for all type definitions.
 *
 * Import from this module to get any type:
 *   import type { Resume, Application, Note } from '../types'
 */

export type { ApiValidationError, ApiError, ApiSuccessResponse } from './api'
export { ApiClientError } from './api'
export type { ResourceType, ResourceRef, GroupedLinks } from './link'
export type {
  ContactInfo,
  WorkExperience,
  Education,
  Skill,
  Resume,
  ResumeVersion,
  ResumeVersionSummary,
} from './resume'
export type { Application, ApplicationSummary, ApplicationContact } from './application'
export type { Accomplishment, AccomplishmentSummary } from './accomplishment'
export type { Note, NoteSummary } from './note'
export type { Contact, ContactSummary } from './contact'
export type { Communication, CommunicationSearchResult } from './communication'
