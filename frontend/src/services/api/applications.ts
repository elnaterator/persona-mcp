/**
 * Job application API endpoints.
 */

import type {
  Application,
  ApplicationContact,
  Communication,
  ApiSuccessResponse,
} from '../../types'
import { API_BASE, fetchWithErrorHandling, handleResponse } from './client'

/**
 * List applications with optional status/tag filter and search query
 */
export async function listApplications(
  status?: string,
  q?: string,
  tags?: string[]
): Promise<Application[]> {
  const params = new URLSearchParams()
  if (status) params.set('status', status)
  if (q) params.set('q', q)
  if (tags && tags.length > 0) tags.forEach((t) => params.append('tag', t))
  const query = params.toString() ? `?${params.toString()}` : ''
  const response = await fetchWithErrorHandling(`${API_BASE}/applications${query}`)
  return handleResponse<Application[]>(response)
}

/**
 * Get a single application by ID
 */
export async function getApplication(id: number): Promise<Application> {
  const response = await fetchWithErrorHandling(`${API_BASE}/applications/${id}`)
  return handleResponse<Application>(response)
}

/**
 * Create a new application
 */
export async function createApplication(
  data: Partial<Application>
): Promise<Application> {
  const response = await fetchWithErrorHandling(`${API_BASE}/applications`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  })
  return handleResponse<Application>(response)
}

/**
 * Update an existing application
 */
export async function updateApplication(
  id: number,
  data: Partial<Application>
): Promise<Application> {
  const response = await fetchWithErrorHandling(`${API_BASE}/applications/${id}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  })
  return handleResponse<Application>(response)
}

/**
 * Delete an application
 */
export async function deleteApplication(id: number): Promise<ApiSuccessResponse> {
  const response = await fetchWithErrorHandling(`${API_BASE}/applications/${id}`, {
    method: 'DELETE',
  })
  return handleResponse<ApiSuccessResponse>(response)
}

// ─── Application contacts API ─────────────────────────────────────────────────

/**
 * List contacts for an application
 */
export async function listAppContacts(appId: number): Promise<ApplicationContact[]> {
  const response = await fetchWithErrorHandling(
    `${API_BASE}/applications/${appId}/contacts`
  )
  return handleResponse<ApplicationContact[]>(response)
}

/**
 * Add a contact to an application
 */
export async function addContact(
  appId: number,
  data: Partial<ApplicationContact>
): Promise<ApplicationContact> {
  const response = await fetchWithErrorHandling(
    `${API_BASE}/applications/${appId}/contacts`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    }
  )
  return handleResponse<ApplicationContact>(response)
}

/**
 * Update a contact for an application
 */
export async function updateAppContact(
  appId: number,
  contactId: number,
  data: Partial<ApplicationContact>
): Promise<ApplicationContact> {
  const response = await fetchWithErrorHandling(
    `${API_BASE}/applications/${appId}/contacts/${contactId}`,
    {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    }
  )
  return handleResponse<ApplicationContact>(response)
}

/**
 * Remove a contact from an application
 */
export async function removeContact(
  appId: number,
  contactId: number
): Promise<ApiSuccessResponse> {
  const response = await fetchWithErrorHandling(
    `${API_BASE}/applications/${appId}/contacts/${contactId}`,
    { method: 'DELETE' }
  )
  return handleResponse<ApiSuccessResponse>(response)
}

// ─── Communications API ───────────────────────────────────────────────────────

/**
 * List communications for an application
 */
export async function listCommunications(appId: number): Promise<Communication[]> {
  const response = await fetchWithErrorHandling(
    `${API_BASE}/applications/${appId}/communications`
  )
  return handleResponse<Communication[]>(response)
}

/**
 * Add a communication to an application
 */
export async function addCommunication(
  appId: number,
  data: Partial<Communication>
): Promise<Communication> {
  const response = await fetchWithErrorHandling(
    `${API_BASE}/applications/${appId}/communications`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    }
  )
  return handleResponse<Communication>(response)
}

/**
 * Update a communication for an application
 */
export async function updateCommunication(
  appId: number,
  commId: number,
  data: Partial<Communication>
): Promise<Communication> {
  const response = await fetchWithErrorHandling(
    `${API_BASE}/applications/${appId}/communications/${commId}`,
    {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    }
  )
  return handleResponse<Communication>(response)
}

/**
 * Remove a communication from an application
 */
export async function removeCommunication(
  appId: number,
  commId: number
): Promise<ApiSuccessResponse> {
  const response = await fetchWithErrorHandling(
    `${API_BASE}/applications/${appId}/communications/${commId}`,
    { method: 'DELETE' }
  )
  return handleResponse<ApiSuccessResponse>(response)
}
