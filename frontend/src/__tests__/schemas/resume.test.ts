import { describe, it, expect } from 'vitest'
import { resumeUpdateSchema } from '../../schemas/resume'

describe('resumeUpdateSchema', () => {
  it('accepts valid input', () => {
    const result = resumeUpdateSchema.safeParse({ label: 'My Resume' })
    expect(result.success).toBe(true)
  })

  it('requires label', () => {
    const result = resumeUpdateSchema.safeParse({ label: '' })
    expect(result.success).toBe(false)
    if (!result.success) expect(result.error.issues[0].path).toContain('label')
  })

  it('trims label', () => {
    const result = resumeUpdateSchema.safeParse({ label: '  Senior  ' })
    expect(result.success).toBe(true)
    if (result.success) expect(result.data.label).toBe('Senior')
  })

  it('accepts optional tags', () => {
    const result = resumeUpdateSchema.safeParse({ label: 'My Resume', tags: ['tech'] })
    expect(result.success).toBe(true)
  })
})
