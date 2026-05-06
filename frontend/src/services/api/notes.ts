/**
 * Notes API endpoints.
 */

import type { Note, NoteSummary, ApiSuccessResponse } from '../../types'
import { API_BASE, fetchWithErrorHandling, handleResponse } from './client'

/**
 * List notes as summaries with optional tag filter (AND logic) and text search
 */
export async function listNotes(
  tags?: string[],
  q?: string
): Promise<NoteSummary[]> {
  const params = new URLSearchParams()
  if (tags && tags.length > 0) tags.forEach((t) => params.append('tag', t))
  if (q) params.set('q', q)
  const query = params.toString() ? `?${params.toString()}` : ''
  const response = await fetchWithErrorHandling(`${API_BASE}/notes${query}`)
  return handleResponse<NoteSummary[]>(response)
}

/**
 * Get a single note by ID (includes full content)
 */
export async function getNote(id: number): Promise<Note> {
  const response = await fetchWithErrorHandling(`${API_BASE}/notes/${id}`)
  return handleResponse<Note>(response)
}

/**
 * Create a new note
 */
export async function createNote(
  data: Partial<Note>
): Promise<Note> {
  const response = await fetchWithErrorHandling(`${API_BASE}/notes`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  })
  return handleResponse<Note>(response)
}

/**
 * Update a note (partial update — only provided fields change)
 */
export async function updateNote(
  id: number,
  data: Partial<Note>
): Promise<Note> {
  const response = await fetchWithErrorHandling(`${API_BASE}/notes/${id}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  })
  return handleResponse<Note>(response)
}

/**
 * Delete a note by ID
 */
export async function deleteNote(id: number): Promise<ApiSuccessResponse> {
  const response = await fetchWithErrorHandling(`${API_BASE}/notes/${id}`, {
    method: 'DELETE',
  })
  return handleResponse<ApiSuccessResponse>(response)
}

/**
 * Get a sorted list of all unique tags used across notes (for autocomplete)
 */
export async function listNoteTags(): Promise<string[]> {
  const response = await fetchWithErrorHandling(`${API_BASE}/notes/tags`)
  return handleResponse<string[]>(response)
}
