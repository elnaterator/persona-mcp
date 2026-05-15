import { describe, it, expect } from 'vitest'
import { accomplishmentCreateSchema, accomplishmentUpdateSchema } from '../../schemas/accomplishment'

describe('accomplishmentCreateSchema', () => {
  it('accepts valid minimal input', () => {
    const result = accomplishmentCreateSchema.safeParse({ title: 'Won award' })
    expect(result.success).toBe(true)
  })

  it('requires title', () => {
    const result = accomplishmentCreateSchema.safeParse({ title: '' })
    expect(result.success).toBe(false)
    if (!result.success) expect(result.error.issues[0].path).toContain('title')
  })

  it('trims title', () => {
    const result = accomplishmentCreateSchema.safeParse({ title: '  Led migration  ' })
    expect(result.success).toBe(true)
    if (result.success) expect(result.data.title).toBe('Led migration')
  })

  it('validates date format', () => {
    const result = accomplishmentCreateSchema.safeParse({ title: 'X', accomplishment_date: '01-2024' })
    expect(result.success).toBe(false)
  })

  it('accepts valid date', () => {
    const result = accomplishmentCreateSchema.safeParse({ title: 'X', accomplishment_date: '2024-01-15' })
    expect(result.success).toBe(true)
  })

  it('normalizes empty date to undefined', () => {
    const result = accomplishmentCreateSchema.safeParse({ title: 'X', accomplishment_date: '' })
    expect(result.success).toBe(true)
    if (result.success) expect(result.data.accomplishment_date).toBeUndefined()
  })

  it('defaults tags to empty array', () => {
    const result = accomplishmentCreateSchema.safeParse({ title: 'X' })
    expect(result.success).toBe(true)
    if (result.success) expect(result.data.tags).toEqual([])
  })
})

describe('accomplishmentUpdateSchema', () => {
  it('all fields optional', () => {
    const result = accomplishmentUpdateSchema.safeParse({})
    expect(result.success).toBe(true)
  })
})
