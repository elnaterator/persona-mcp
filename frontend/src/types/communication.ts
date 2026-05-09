/**
 * TypeScript type definitions for communications.
 */

export interface Communication {
  id: number
  contact_ref_id: number
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
  parentType: 'contact'
  parentId: number
  parentName: string
}
