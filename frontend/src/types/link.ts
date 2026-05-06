/**
 * Resource link types for cross-resource linking.
 */

export type ResourceType = 'application' | 'accomplishment' | 'resume' | 'note' | 'contact'

export interface ResourceRef {
  type: ResourceType
  id: number
  name: string
  updatedAt?: string | null
}

export type GroupedLinks = Partial<Record<ResourceType, ResourceRef[]>>
