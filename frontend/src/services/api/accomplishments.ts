/**
 * Accomplishments API endpoints.
 */

import type { Accomplishment, AccomplishmentSummary, ApiSuccessResponse } from '../../types'
import { API_BASE, fetchWithErrorHandling, handleResponse } from './client'

/**
 * List accomplishments as summaries with optional tag filter (AND logic) and text search
 */
export async function listAccomplishments(
  tags?: string[],
  q?: string
): Promise<AccomplishmentSummary[]> {
  const params = new URLSearchParams()
  if (tags && tags.length > 0) tags.forEach((t) => params.append('tag', t))
  if (q) params.set('q', q)
  const query = params.toString() ? `?${params.toString()}` : ''
  const response = await fetchWithErrorHandling(`${API_BASE}/accomplishments${query}`)
  return handleResponse<AccomplishmentSummary[]>(response)
}

/**
 * Get a single accomplishment by ID (includes full STAR fields)
 */
export async function getAccomplishment(id: number): Promise<Accomplishment> {
  const response = await fetchWithErrorHandling(`${API_BASE}/accomplishments/${id}`)
  return handleResponse<Accomplishment>(response)
}

/**
 * Create a new accomplishment
 */
export async function createAccomplishment(
  data: Partial<Accomplishment>
): Promise<Accomplishment> {
  const response = await fetchWithErrorHandling(`${API_BASE}/accomplishments`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  })
  return handleResponse<Accomplishment>(response)
}

/**
 * Update an accomplishment (partial update — only provided fields change)
 */
export async function updateAccomplishment(
  id: number,
  data: Partial<Accomplishment>
): Promise<Accomplishment> {
  const response = await fetchWithErrorHandling(`${API_BASE}/accomplishments/${id}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  })
  return handleResponse<Accomplishment>(response)
}

/**
 * Delete an accomplishment by ID
 */
export async function deleteAccomplishment(id: number): Promise<ApiSuccessResponse> {
  const response = await fetchWithErrorHandling(`${API_BASE}/accomplishments/${id}`, {
    method: 'DELETE',
  })
  return handleResponse<ApiSuccessResponse>(response)
}

/**
 * Get a sorted list of all unique tags used across accomplishments (for autocomplete)
 */
export async function listAccomplishmentTags(): Promise<string[]> {
  const response = await fetchWithErrorHandling(`${API_BASE}/accomplishments/tags`)
  return handleResponse<string[]>(response)
}
