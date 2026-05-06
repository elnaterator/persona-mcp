/**
 * Networking contacts API endpoints and contact communications.
 */

import type {
  Contact,
  ContactSummary,
  Communication,
  CommunicationSearchResult,
  ApiSuccessResponse,
} from '../../types'
import { API_BASE, fetchWithErrorHandling, handleResponse } from './client'

function _mapComm(raw: Record<string, unknown>): Communication {
  return {
    ...(raw as unknown as Communication),
    app_id: raw.app_id as number | null | undefined,
    contact_ref_id: raw.contact_ref_id as number | null | undefined,
    tags: (raw.tags as string[]) ?? [],
  }
}

/**
 * List contacts as summaries with optional tag filter (AND logic) and text search
 */
export async function listContacts(
  tags?: string[],
  q?: string
): Promise<ContactSummary[]> {
  const params = new URLSearchParams()
  if (tags && tags.length > 0) tags.forEach((t) => params.append('tag', t))
  if (q) params.set('q', q)
  const query = params.toString() ? `?${params.toString()}` : ''
  const response = await fetchWithErrorHandling(`${API_BASE}/contacts${query}`)
  return handleResponse<ContactSummary[]>(response)
}

/**
 * Get a single contact by ID (includes full notes)
 */
export async function getContact(id: number): Promise<Contact> {
  const response = await fetchWithErrorHandling(`${API_BASE}/contacts/${id}`)
  return handleResponse<Contact>(response)
}

/**
 * Create a new contact
 */
export async function createContact(data: Partial<Contact>): Promise<Contact> {
  const response = await fetchWithErrorHandling(`${API_BASE}/contacts`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  })
  return handleResponse<Contact>(response)
}

/**
 * Update a contact (partial update — only provided fields change)
 */
export async function updateContact(
  id: number,
  data: Partial<Contact>
): Promise<Contact> {
  const response = await fetchWithErrorHandling(`${API_BASE}/contacts/${id}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  })
  return handleResponse<Contact>(response)
}

/**
 * Delete a contact by ID
 */
export async function deleteContact(id: number): Promise<ApiSuccessResponse> {
  const response = await fetchWithErrorHandling(`${API_BASE}/contacts/${id}`, {
    method: 'DELETE',
  })
  return handleResponse<ApiSuccessResponse>(response)
}

/**
 * Get a sorted list of all unique tags used across contacts (for autocomplete)
 */
export async function listContactTags(): Promise<string[]> {
  const response = await fetchWithErrorHandling(`${API_BASE}/contacts/tags`)
  return handleResponse<string[]>(response)
}

// ─── Contact Communications API ───────────────────────────────────────────────

export async function listContactCommunications(
  contactId: number
): Promise<Communication[]> {
  const response = await fetchWithErrorHandling(
    `${API_BASE}/contacts/${contactId}/communications`
  )
  const data = await handleResponse<unknown[]>(response)
  return data.map((r) => _mapComm(r as Record<string, unknown>))
}

export async function addContactCommunication(
  contactId: number,
  data: Partial<Communication>
): Promise<Communication> {
  const response = await fetchWithErrorHandling(
    `${API_BASE}/contacts/${contactId}/communications`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    }
  )
  const raw = await handleResponse<Record<string, unknown>>(response)
  return _mapComm(raw)
}

export async function updateContactCommunication(
  contactId: number,
  commId: number,
  data: Partial<Communication>
): Promise<Communication> {
  const response = await fetchWithErrorHandling(
    `${API_BASE}/contacts/${contactId}/communications/${commId}`,
    {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    }
  )
  const raw = await handleResponse<Record<string, unknown>>(response)
  return _mapComm(raw)
}

export async function removeContactCommunication(
  contactId: number,
  commId: number
): Promise<ApiSuccessResponse> {
  const response = await fetchWithErrorHandling(
    `${API_BASE}/contacts/${contactId}/communications/${commId}`,
    { method: 'DELETE' }
  )
  return handleResponse<ApiSuccessResponse>(response)
}

export async function searchCommunications(params: {
  q?: string
  tags?: string[]
  parent?: 'application' | 'contact' | 'all'
}): Promise<CommunicationSearchResult[]> {
  const qs = new URLSearchParams()
  if (params.q) qs.set('q', params.q)
  if (params.tags?.length) params.tags.forEach((t) => qs.append('tag', t))
  if (params.parent && params.parent !== 'all') qs.set('parent', params.parent)
  const response = await fetchWithErrorHandling(
    `${API_BASE}/communications${qs.toString() ? `?${qs}` : ''}`
  )
  const data = await handleResponse<Record<string, unknown>[]>(response)
  return data.map((r) => ({
    ...(_mapComm(r) as CommunicationSearchResult),
    parentType: r.parent_type as 'application' | 'contact',
    parentId: r.parent_id as number,
    parentName: r.parent_name as string,
  }))
}
