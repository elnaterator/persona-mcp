import { describe, expect, it } from 'vitest'
import {
  accomplishmentKeys,
  applicationKeys,
  contactKeys,
  noteKeys,
  resumeKeys,
  tagKeys,
} from '../../../hooks/queries'

describe('query keys', () => {
  it('note keys hierarchy', () => {
    expect(noteKeys.all).toEqual(['notes'])
    expect(noteKeys.lists()).toEqual(['notes', 'list'])
    expect(noteKeys.list({ q: 'x' })).toEqual(['notes', 'list', { q: 'x' }])
    expect(noteKeys.detail(7)).toEqual(['notes', 'detail', 7])
  })

  it('application keys hierarchy', () => {
    expect(applicationKeys.detail(3)).toEqual(['applications', 'detail', 3])
    expect(applicationKeys.list({ status: 'Applied' })).toEqual([
      'applications',
      'list',
      { status: 'Applied' },
    ])
  })

  it('accomplishment keys', () => {
    expect(accomplishmentKeys.detail(1)).toEqual(['accomplishments', 'detail', 1])
  })

  it('contact keys + comms key', () => {
    expect(contactKeys.detail(2)).toEqual(['contacts', 'detail', 2])
    expect(contactKeys.comms(2)).toEqual(['contacts', 'detail', 2, 'communications'])
  })

  it('resume keys', () => {
    expect(resumeKeys.detail(9)).toEqual(['resumes', 'detail', 9])
    expect(resumeKeys.list()).toEqual(['resumes', 'list'])
  })

  it('tag keys', () => {
    expect(tagKeys.list()).toEqual(['tags', 'list'])
  })
})
