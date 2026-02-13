/**
 * Tests for API client module.
 *
 * Mocks fetch to verify correct URLs, methods, headers, and error handling.
 */

import { describe, it, expect, beforeEach, vi } from 'vitest'
import * as api from '../../services/api'
import type { ContactInfo, WorkExperience, Education, Skill } from '../../types/resume'

// Mock fetch globally
global.fetch = vi.fn()

describe('API Client', () => {
  beforeEach(() => {
    // Reset mocks before each test
    vi.clearAllMocks()
  })

  describe('getResume', () => {
    it('should fetch the full resume', async () => {
      const mockResume = {
        contact: { name: 'John Doe', email: null, phone: null, location: null, linkedin: null, website: null, github: null },
        summary: 'Test summary',
        experience: [],
        education: [],
        skills: [],
      }

      ;(global.fetch as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
        ok: true,
        json: async () => mockResume,
      })

      const result = await api.getResume()

      expect(global.fetch).toHaveBeenCalledWith('/api/resume', undefined)
      expect(result).toEqual(mockResume)
    })

    it('should throw ApiClientError on HTTP error', async () => {
      ;(global.fetch as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
        ok: false,
        status: 500,
        statusText: 'Internal Server Error',
        json: async () => ({ detail: 'Database error' }),
      })

      await expect(api.getResume()).rejects.toThrow('Database error')
    })
  })

  describe('getSection', () => {
    it('should fetch a specific section', async () => {
      const mockContact: ContactInfo = {
        name: 'Jane Doe',
        email: 'jane@example.com',
        phone: null,
        location: null,
        linkedin: null,
        website: null,
        github: null,
      }

      ;(global.fetch as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
        ok: true,
        json: async () => mockContact,
      })

      const result = await api.getSection('contact')

      expect(global.fetch).toHaveBeenCalledWith('/api/resume/contact', undefined)
      expect(result).toEqual(mockContact)
    })
  })

  describe('updateContact', () => {
    it('should send PUT request with contact data', async () => {
      const updateData: Partial<ContactInfo> = {
        name: 'John Updated',
        email: 'john@updated.com',
      }

      const mockResponse = { message: 'Updated contact fields: name, email' }

      ;(global.fetch as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse,
      })

      const result = await api.updateContact(updateData)

      expect(global.fetch).toHaveBeenCalledWith('/api/resume/contact', {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(updateData),
      })
      expect(result).toEqual(mockResponse)
    })

    it('should handle validation errors', async () => {
      ;(global.fetch as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
        ok: false,
        status: 422,
        statusText: 'Unprocessable Entity',
        json: async () => ({ detail: 'Invalid email format' }),
      })

      await expect(api.updateContact({ email: 'invalid' })).rejects.toThrow(
        'Invalid email format'
      )
    })
  })

  describe('updateSummary', () => {
    it('should send PUT request with summary text', async () => {
      const summaryText = 'Updated summary'
      const mockResponse = { message: 'Updated summary' }

      ;(global.fetch as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse,
      })

      const result = await api.updateSummary(summaryText)

      expect(global.fetch).toHaveBeenCalledWith('/api/resume/summary', {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ text: summaryText }),
      })
      expect(result).toEqual(mockResponse)
    })

    it('should reject empty summary', async () => {
      ;(global.fetch as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
        ok: false,
        status: 422,
        statusText: 'Unprocessable Entity',
        json: async () => ({ detail: 'Summary text cannot be empty' }),
      })

      await expect(api.updateSummary('')).rejects.toThrow(
        'Summary text cannot be empty'
      )
    })
  })

  describe('addEntry', () => {
    it('should add experience entry', async () => {
      const newExperience: WorkExperience = {
        title: 'Software Engineer',
        company: 'Tech Corp',
        start_date: '2020-01',
        end_date: null,
        location: 'Remote',
        highlights: ['Built features'],
      }

      const mockResponse = {
        message: 'Added experience entry: Software Engineer at Tech Corp',
      }

      ;(global.fetch as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse,
      })

      const result = await api.addEntry('experience', newExperience)

      expect(global.fetch).toHaveBeenCalledWith('/api/resume/experience/entries', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(newExperience),
      })
      expect(result).toEqual(mockResponse)
    })

    it('should add skill entry', async () => {
      const newSkill: Skill = {
        name: 'TypeScript',
        category: 'Programming Languages',
      }

      const mockResponse = { message: 'Added skill entry: TypeScript' }

      ;(global.fetch as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse,
      })

      const result = await api.addEntry('skills', newSkill)

      expect(global.fetch).toHaveBeenCalledWith('/api/resume/skills/entries', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(newSkill),
      })
      expect(result).toEqual(mockResponse)
    })
  })

  describe('updateEntry', () => {
    it('should update entry at specific index', async () => {
      const updateData: Partial<Education> = {
        honors: 'Summa Cum Laude',
      }

      const mockResponse = {
        message: 'Updated education entry at index 0: University',
      }

      ;(global.fetch as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse,
      })

      const result = await api.updateEntry('education', 0, updateData)

      expect(global.fetch).toHaveBeenCalledWith('/api/resume/education/entries/0', {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(updateData),
      })
      expect(result).toEqual(mockResponse)
    })

    it('should handle invalid index', async () => {
      ;(global.fetch as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
        ok: false,
        status: 404,
        statusText: 'Not Found',
        json: async () => ({ detail: 'Index out of range' }),
      })

      await expect(api.updateEntry('experience', 999, {})).rejects.toThrow(
        'Index out of range'
      )
    })
  })

  describe('removeEntry', () => {
    it('should delete entry at specific index', async () => {
      const mockResponse = {
        message: 'Removed experience entry: Old Job at Old Company',
      }

      ;(global.fetch as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse,
      })

      const result = await api.removeEntry('experience', 2)

      expect(global.fetch).toHaveBeenCalledWith('/api/resume/experience/entries/2', {
        method: 'DELETE',
      })
      expect(result).toEqual(mockResponse)
    })

    it('should handle not found error', async () => {
      ;(global.fetch as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
        ok: false,
        status: 404,
        statusText: 'Not Found',
        json: async () => ({ detail: 'Entry not found' }),
      })

      await expect(api.removeEntry('skills', 10)).rejects.toThrow('Entry not found')
    })
  })

  describe('Error handling', () => {
    it('should handle network errors', async () => {
      ;(global.fetch as ReturnType<typeof vi.fn>).mockRejectedValueOnce(
        new Error('Network error')
      )

      await expect(api.getResume()).rejects.toThrow('Network error')
    })

    it('should handle malformed JSON error responses', async () => {
      ;(global.fetch as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
        ok: false,
        status: 500,
        statusText: 'Internal Server Error',
        json: async () => {
          throw new Error('Invalid JSON')
        },
      })

      await expect(api.getResume()).rejects.toThrow()
    })
  })
})
