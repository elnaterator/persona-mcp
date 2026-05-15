import { z } from 'zod'

export const resumeUpdateSchema = z.object({
  label: z.string().trim().min(1, 'Label is required').max(200),
  tags: z.array(z.string()).optional(),
})

export type ResumeUpdateInput = z.infer<typeof resumeUpdateSchema>
