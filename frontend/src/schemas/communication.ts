import { z } from 'zod'

const optionalTrimmed = () =>
  z
    .string()
    .trim()
    .transform((v) => v || undefined)
    .optional()

const isoDate = z
  .string()
  .trim()
  .regex(/^\d{4}-\d{2}-\d{2}$/, 'Must be YYYY-MM-DD')

export const COMM_TYPES = ['email', 'phone', 'interview_note', 'other'] as const
export const COMM_DIRECTIONS = ['sent', 'received'] as const
export const COMM_STATUSES = ['draft', 'ready', 'sent', 'archived'] as const

export const communicationCreateSchema = z.object({
  type: z.enum(COMM_TYPES),
  direction: z.enum(COMM_DIRECTIONS),
  subject: optionalTrimmed(),
  body: optionalTrimmed(),
  date: isoDate,
  status: z.enum(COMM_STATUSES),
  tags: z.array(z.string()).default([]),
})

export type CommunicationCreateInput = z.infer<typeof communicationCreateSchema>

export const communicationUpdateSchema = communicationCreateSchema.partial()
export type CommunicationUpdateInput = z.infer<typeof communicationUpdateSchema>
