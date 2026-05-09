import { useState, useEffect, useCallback } from 'react'
import type { GroupedLinks, ResourceType } from '../types'
import { linkResources, unlinkResources } from '../services/api'

// Note: links are embedded in the resource detail responses as `links` field
// This hook is for cases where you need to fetch/manage links independently
export interface UseLinksState {
  links: GroupedLinks
  loading: boolean
  link: (bType: ResourceType, bId: number) => Promise<void>
  unlink: (bType: ResourceType, bId: number) => Promise<void>
  setLinks: (links: GroupedLinks) => void
}

export function useLinks(
  resourceType: ResourceType,
  resourceId: number | undefined,
  initialLinks?: GroupedLinks
): UseLinksState {
  const [links, setLinks] = useState<GroupedLinks>(initialLinks ?? {})
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (initialLinks) setLinks(initialLinks)
  }, [initialLinks])

  const link = useCallback(async (bType: ResourceType, bId: number) => {
    if (!resourceId) return
    setLoading(true)
    try {
      await linkResources(resourceType, resourceId, bType, bId)
    } finally {
      setLoading(false)
    }
  }, [resourceType, resourceId])

  const unlink = useCallback(async (bType: ResourceType, bId: number) => {
    if (!resourceId) return
    setLoading(true)
    try {
      await unlinkResources(resourceType, resourceId, bType, bId)
    } finally {
      setLoading(false)
    }
  }, [resourceType, resourceId])

  return { links, loading, link, unlink, setLinks }
}
