/**
 * Unified tags API endpoints.
 */

import { API_BASE, fetchWithErrorHandling, handleResponse } from './client'

/**
 * Get a sorted, deduplicated list of all tags across all resource types
 */
export async function listAllTags(): Promise<string[]> {
  const response = await fetchWithErrorHandling(`${API_BASE}/tags`)
  return handleResponse<string[]>(response)
}

/**
 * Get all unique tags used across applications
 */
export async function listApplicationTags(): Promise<string[]> {
  const response = await fetchWithErrorHandling(`${API_BASE}/applications/tags`)
  return handleResponse<string[]>(response)
}

/**
 * Get all unique tags used across resume versions
 */
export async function listResumeTags(): Promise<string[]> {
  const response = await fetchWithErrorHandling(`${API_BASE}/resumes/tags`)
  return handleResponse<string[]>(response)
}
