import { useMutation, useQueryClient } from '@tanstack/react-query'
import type { ResourceType } from '../../types'
import { linkResources, unlinkResources } from '../../services/api'
import { accomplishmentKeys } from './accomplishments'
import { applicationKeys } from './applications'
import { contactKeys } from './contacts'
import { noteKeys } from './notes'
import { resumeKeys } from './resumes'

const KEYS_BY_TYPE: Record<ResourceType, { lists: () => readonly unknown[]; detail: (id: number) => readonly unknown[] }> = {
  application: { lists: applicationKeys.lists, detail: applicationKeys.detail },
  accomplishment: { lists: accomplishmentKeys.lists, detail: accomplishmentKeys.detail },
  resume: { lists: resumeKeys.lists, detail: resumeKeys.detail },
  note: { lists: noteKeys.lists, detail: noteKeys.detail },
  contact: { lists: contactKeys.lists, detail: contactKeys.detail },
}

interface LinkArgs {
  aType: ResourceType
  aId: number
  bType: ResourceType
  bId: number
}

export function useLinkMutations() {
  const qc = useQueryClient()
  const invalidateBoth = ({ aType, aId, bType, bId }: LinkArgs) => {
    const a = KEYS_BY_TYPE[aType]
    const b = KEYS_BY_TYPE[bType]
    qc.invalidateQueries({ queryKey: a.detail(aId) })
    qc.invalidateQueries({ queryKey: b.detail(bId) })
    qc.invalidateQueries({ queryKey: a.lists() })
    qc.invalidateQueries({ queryKey: b.lists() })
  }
  const link = useMutation({
    mutationFn: ({ aType, aId, bType, bId }: LinkArgs) =>
      linkResources(aType, aId, bType, bId),
    onSuccess: (_d, vars) => invalidateBoth(vars),
  })
  const unlink = useMutation({
    mutationFn: ({ aType, aId, bType, bId }: LinkArgs) =>
      unlinkResources(aType, aId, bType, bId),
    onSuccess: (_d, vars) => invalidateBoth(vars),
  })
  return { link, unlink }
}
