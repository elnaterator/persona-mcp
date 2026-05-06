/**
 * TypeScript type definitions for communications.
 */

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
