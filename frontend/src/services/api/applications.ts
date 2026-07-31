/**
 * Job application API endpoints.
 */

import type { Application, ApiSuccessResponse } from '../../types'
import { API_BASE, fetchWithErrorHandling, handleResponse } from './client'

/**
 * List applications with optional status/tag filter and search query
 */
export async function listApplications(
  status?: string[],
  q?: string,
  tags?: string[]
): Promise<Application[]> {
  const params = new URLSearchParams()
  if (status && status.length > 0) status.forEach((s) => params.append('status', s))
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
