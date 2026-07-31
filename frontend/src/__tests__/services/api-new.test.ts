/**
 * Tests for the new job application API functions.
 */

import { describe, it, expect, beforeEach, vi } from 'vitest'
import * as api from '../../services/api'

// Mock fetch globally
global.fetch = vi.fn()

const mockFetch = (data: unknown, ok = true, status = 200) => {
  ;(global.fetch as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
    ok,
    status,
    statusText: ok ? 'OK' : 'Error',
    json: async () => data,
  })
}

describe('Resume Version API', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('listResumes', () => {
    it('fetches /api/resumes', async () => {
      mockFetch([])
      await api.listResumes()
      expect(global.fetch).toHaveBeenCalledWith('/api/resumes', undefined)
    })
  })

  describe('getResumeVersion', () => {
    it('fetches /api/resumes/:id', async () => {
      mockFetch({ id: 1, label: 'Main' })
      await api.getResumeVersion(1)
      expect(global.fetch).toHaveBeenCalledWith('/api/resumes/1', undefined)
    })
  })

  describe('getDefaultResume', () => {
    it('fetches /api/resumes/default', async () => {
      mockFetch({ id: 1, label: 'Main', is_default: true })
      await api.getDefaultResume()
      expect(global.fetch).toHaveBeenCalledWith('/api/resumes/default', undefined)
    })
  })

  describe('createResume', () => {
    it('sends POST to /api/resumes with label', async () => {
      mockFetch({ id: 2, label: 'New Version' })
      await api.createResume('New Version')
      expect(global.fetch).toHaveBeenCalledWith('/api/resumes', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ label: 'New Version' }),
      })
    })
  })

  describe('deleteResume', () => {
    it('sends DELETE to /api/resumes/:id', async () => {
      mockFetch({ message: 'Deleted' })
      await api.deleteResume(3)
      expect(global.fetch).toHaveBeenCalledWith('/api/resumes/3', { method: 'DELETE' })
    })
  })

  describe('setDefaultResume', () => {
    it('sends POST to /api/resumes/:id/default', async () => {
      mockFetch({ message: 'Updated' })
      await api.setDefaultResume(2)
      expect(global.fetch).toHaveBeenCalledWith('/api/resumes/2/default', { method: 'POST' })
    })
  })

  describe('updateResumeLabel', () => {
    it('sends PATCH to /api/resumes/:id with label', async () => {
      mockFetch({ id: 1, label: 'Updated Label' })
      await api.updateResumeLabel(1, 'Updated Label')
      expect(global.fetch).toHaveBeenCalledWith('/api/resumes/1', {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ label: 'Updated Label' }),
      })
    })
  })

  describe('updateVersionContact', () => {
    it('sends PUT to /api/resumes/:id/contact', async () => {
      mockFetch({ message: 'Updated' })
      await api.updateVersionContact(1, { name: 'Jane' })
      expect(global.fetch).toHaveBeenCalledWith('/api/resumes/1/contact', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: 'Jane' }),
      })
    })
  })

  describe('updateVersionSummary', () => {
    it('sends PUT to /api/resumes/:id/summary', async () => {
      mockFetch({ message: 'Updated' })
      await api.updateVersionSummary(1, 'New summary')
      expect(global.fetch).toHaveBeenCalledWith('/api/resumes/1/summary', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: 'New summary' }),
      })
    })
  })

  describe('addVersionEntry', () => {
    it('sends POST to version-scoped section endpoint', async () => {
      mockFetch({ message: 'Added' })
      const data = { name: 'TypeScript', category: 'Languages' }
      await api.addVersionEntry(1, 'skills', data)
      expect(global.fetch).toHaveBeenCalledWith('/api/resumes/1/skills/entries', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
      })
    })
  })

  describe('updateVersionEntry', () => {
    it('sends PUT to version-scoped section entry endpoint', async () => {
      mockFetch({ message: 'Updated' })
      const data = { name: 'TypeScript Updated' }
      await api.updateVersionEntry(1, 'skills', 0, data)
      expect(global.fetch).toHaveBeenCalledWith('/api/resumes/1/skills/entries/0', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
      })
    })
  })

  describe('removeVersionEntry', () => {
    it('sends DELETE to version-scoped section entry endpoint', async () => {
      mockFetch({ message: 'Removed' })
      await api.removeVersionEntry(1, 'experience', 2)
      expect(global.fetch).toHaveBeenCalledWith('/api/resumes/1/experience/entries/2', {
        method: 'DELETE',
      })
    })
  })
})

describe('Application API', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('listApplications', () => {
    it('fetches /api/applications without params', async () => {
      mockFetch([])
      await api.listApplications()
      expect(global.fetch).toHaveBeenCalledWith('/api/applications', undefined)
    })

    it('fetches with status filter', async () => {
      mockFetch([])
      await api.listApplications(['Applied'])
      expect(global.fetch).toHaveBeenCalledWith('/api/applications?status=Applied', undefined)
    })

    it('fetches with multiple statuses', async () => {
      mockFetch([])
      await api.listApplications(['Applied', 'Interview'])
      expect(global.fetch).toHaveBeenCalledWith(
        '/api/applications?status=Applied&status=Interview',
        undefined
      )
    })

    it('fetches with search query', async () => {
      mockFetch([])
      await api.listApplications(undefined, 'google')
      expect(global.fetch).toHaveBeenCalledWith('/api/applications?q=google', undefined)
    })

    it('fetches with both status and query', async () => {
      mockFetch([])
      await api.listApplications(['Applied'], 'google')
      expect(global.fetch).toHaveBeenCalledWith(
        '/api/applications?status=Applied&q=google',
        undefined
      )
    })
  })

  describe('getApplication', () => {
    it('fetches /api/applications/:id', async () => {
      mockFetch({ id: 5 })
      await api.getApplication(5)
      expect(global.fetch).toHaveBeenCalledWith('/api/applications/5', undefined)
    })
  })

  describe('createApplication', () => {
    it('sends POST with application data', async () => {
      const data = { company: 'Acme', position: 'Engineer', status: 'Applied' }
      mockFetch({ id: 1, ...data })
      await api.createApplication(data)
      expect(global.fetch).toHaveBeenCalledWith('/api/applications', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
      })
    })
  })

  describe('updateApplication', () => {
    it('sends PATCH with updated fields', async () => {
      const data = { status: 'Interview' }
      mockFetch({ id: 1, ...data })
      await api.updateApplication(1, data)
      expect(global.fetch).toHaveBeenCalledWith('/api/applications/1', {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
      })
    })
  })

  describe('deleteApplication', () => {
    it('sends DELETE to /api/applications/:id', async () => {
      mockFetch({ message: 'Deleted' })
      await api.deleteApplication(3)
      expect(global.fetch).toHaveBeenCalledWith('/api/applications/3', { method: 'DELETE' })
    })
  })
})

