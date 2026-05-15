import { describe, it, expect } from 'vitest'
import { noteCreateSchema, noteUpdateSchema } from '../../schemas/note'

describe('noteCreateSchema', () => {
  it('accepts valid minimal input', () => {
    const result = noteCreateSchema.safeParse({ title: 'My note' })
    expect(result.success).toBe(true)
  })

  it('requires title', () => {
    const result = noteCreateSchema.safeParse({ title: '' })
    expect(result.success).toBe(false)
    if (!result.success) expect(result.error.issues[0].path).toContain('title')
  })

  it('trims title', () => {
    const result = noteCreateSchema.safeParse({ title: '  My note  ' })
    expect(result.success).toBe(true)
    if (result.success) expect(result.data.title).toBe('My note')
  })

  it('normalizes empty content to undefined', () => {
    const result = noteCreateSchema.safeParse({ title: 'X', content: '' })
    expect(result.success).toBe(true)
    if (result.success) expect(result.data.content).toBeUndefined()
  })

  it('defaults tags to empty array', () => {
    const result = noteCreateSchema.safeParse({ title: 'X' })
    expect(result.success).toBe(true)
    if (result.success) expect(result.data.tags).toEqual([])
  })
})

describe('noteUpdateSchema', () => {
  it('all fields optional', () => {
    const result = noteUpdateSchema.safeParse({})
    expect(result.success).toBe(true)
  })
})
