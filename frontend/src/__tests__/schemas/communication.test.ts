import { describe, it, expect } from 'vitest'
import { communicationCreateSchema, communicationUpdateSchema } from '../../schemas/communication'

describe('communicationCreateSchema', () => {
  const valid = {
    type: 'email' as const,
    direction: 'sent' as const,
    date: '2024-01-15',
    status: 'draft' as const,
  }

  it('accepts valid minimal input', () => {
    const result = communicationCreateSchema.safeParse(valid)
    expect(result.success).toBe(true)
  })

  it('validates date format', () => {
    const result = communicationCreateSchema.safeParse({ ...valid, date: '01/15/2024' })
    expect(result.success).toBe(false)
    if (!result.success) expect(result.error.issues[0].path).toContain('date')
  })

  it('rejects invalid type enum', () => {
    const result = communicationCreateSchema.safeParse({ ...valid, type: 'letter' })
    expect(result.success).toBe(false)
  })

  it('normalizes empty subject to undefined', () => {
    const result = communicationCreateSchema.safeParse({ ...valid, subject: '' })
    expect(result.success).toBe(true)
    if (result.success) expect(result.data.subject).toBeUndefined()
  })

  it('defaults tags to empty array', () => {
    const result = communicationCreateSchema.safeParse(valid)
    expect(result.success).toBe(true)
    if (result.success) expect(result.data.tags).toEqual([])
  })
})

describe('communicationUpdateSchema', () => {
  it('all fields optional', () => {
    const result = communicationUpdateSchema.safeParse({})
    expect(result.success).toBe(true)
  })
})
