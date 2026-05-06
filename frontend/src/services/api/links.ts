/**
 * Resource linking API endpoints.
 */

import type { GroupedLinks, ResourceRef, ResourceType, ApiSuccessResponse } from '../../types'
import { API_BASE, fetchWithErrorHandling, handleResponse } from './client'

export function _mapRef(raw: Record<string, unknown>): ResourceRef {
  return {
    type: raw.type as ResourceType,
    id: raw.id as number,
    name: raw.name as string,
    updatedAt: raw.updated_at as string | null | undefined,
  }
}

export function mapGroupedLinks(
  raw: Record<string, unknown[]> | undefined
): GroupedLinks {
  if (!raw) return {}
  const result: GroupedLinks = {}
  for (const [type, refs] of Object.entries(raw)) {
    result[type as ResourceType] = (refs as Record<string, unknown>[]).map(_mapRef)
  }
  return result
}

export async function linkResources(
  aType: ResourceType,
  aId: number,
  bType: ResourceType,
  bId: number
): Promise<ApiSuccessResponse> {
  const response = await fetchWithErrorHandling(`${API_BASE}/links`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ a_type: aType, a_id: aId, b_type: bType, b_id: bId }),
  })
  return handleResponse<ApiSuccessResponse>(response)
}

export async function unlinkResources(
  aType: ResourceType,
  aId: number,
  bType: ResourceType,
  bId: number
): Promise<void> {
  const response = await fetchWithErrorHandling(`${API_BASE}/links`, {
    method: 'DELETE',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ a_type: aType, a_id: aId, b_type: bType, b_id: bId }),
  })
  if (!response.ok && response.status !== 204) {
    await handleResponse<void>(response)
  }
}
