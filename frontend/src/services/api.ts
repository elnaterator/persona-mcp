/**
 * API client for resume backend.
 *
 * Thin wrapper around fetch API with JSON parsing and error handling.
 */

import type {
  Accomplishment,
  AccomplishmentSummary,
  ApiError,
  ApiSuccessResponse,
  Application,
  ApplicationContact,
  Communication,
  ContactInfo,
  Education,
  Resume,
  ResumeVersion,
  ResumeVersionSummary,
  Skill,
  WorkExperience,
} from '../types/resume'

let _getToken: (() => Promise<string | null>) | null = null

export function setTokenGetter(getter: (() => Promise<string | null>) | null): void {
  _getToken = getter
}

const API_BASE = '/api'

/**
 * Custom error class for API errors
 */
export class ApiClientError extends Error {
  constructor(
    message: string,
    public status: number,
    public detail?: string
  ) {
    super(message)
    this.name = 'ApiClientError'
  }
}

/**
 * Handle fetch response and extract JSON or error
 */
async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    let detail = `HTTP ${response.status}: ${response.statusText}`

    try {
      const errorData = (await response.json()) as ApiError
      if (errorData.detail) {
        detail = errorData.detail
      }
    } catch {
      // If JSON parsing fails, use the status text
    }

    throw new ApiClientError(detail, response.status, detail)
  }

  return response.json() as Promise<T>
}

/**
 * Wrapper to handle network errors (TypeError from fetch)
 * Converts network failures into user-friendly error messages.
 * Attaches a Bearer token from the token getter if one is configured.
 */
async function fetchWithErrorHandling(
  url: string,
  options?: RequestInit
): Promise<Response> {
  try {
    let fetchOptions: RequestInit | undefined = options
    if (_getToken) {
      const token = await _getToken()
      if (token) {
        const headers: Record<string, string> = {
          ...(options?.headers as Record<string, string> | undefined),
          Authorization: `Bearer ${token}`,
        }
        fetchOptions = { ...options, headers }
      } else {
        // User signed out — redirect to home
        window.location.href = '/'
        throw new ApiClientError('Not authenticated', 401, 'Not authenticated')
      }
    }
    return await fetch(url, fetchOptions)
  } catch (error) {
    if (error instanceof ApiClientError) throw error
    if (error instanceof TypeError) {
      throw new ApiClientError(
        'Network error: Unable to connect to server. Please check your connection and try again.',
        0,
        'Network error: Failed to fetch'
      )
    }
    throw error
  }
}

/**
 * Get the full resume
 */
export async function getResume(): Promise<Resume> {
  const response = await fetchWithErrorHandling(`${API_BASE}/resume`)
  return handleResponse<Resume>(response)
}

/**
 * Get a specific section of the resume
 */
export async function getSection(
  section: 'contact' | 'summary' | 'experience' | 'education' | 'skills'
): Promise<ContactInfo | string | WorkExperience[] | Education[] | Skill[]> {
  const response = await fetchWithErrorHandling(`${API_BASE}/resume/${section}`)
  return handleResponse(response)
}

/**
 * Update contact information
 */
export async function updateContact(
  data: Partial<ContactInfo>
): Promise<ApiSuccessResponse> {
  const response = await fetchWithErrorHandling(`${API_BASE}/resume/contact`, {
    method: 'PUT',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(data),
  })
  return handleResponse<ApiSuccessResponse>(response)
}

/**
 * Update summary text
 */
export async function updateSummary(text: string): Promise<ApiSuccessResponse> {
  const response = await fetchWithErrorHandling(`${API_BASE}/resume/summary`, {
    method: 'PUT',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ text }),
  })
  return handleResponse<ApiSuccessResponse>(response)
}

/**
 * Add a new entry to a list-based section
 */
export async function addEntry(
  section: 'experience' | 'education' | 'skills',
  data: WorkExperience | Education | Skill
): Promise<ApiSuccessResponse> {
  const response = await fetchWithErrorHandling(`${API_BASE}/resume/${section}/entries`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(data),
  })
  return handleResponse<ApiSuccessResponse>(response)
}

/**
 * Update an existing entry in a list-based section
 */
export async function updateEntry(
  section: 'experience' | 'education' | 'skills',
  index: number,
  data: Partial<WorkExperience | Education | Skill>
): Promise<ApiSuccessResponse> {
  const response = await fetchWithErrorHandling(
    `${API_BASE}/resume/${section}/entries/${index}`,
    {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data),
    }
  )
  return handleResponse<ApiSuccessResponse>(response)
}

/**
 * Remove an entry from a list-based section
 */
export async function removeEntry(
  section: 'experience' | 'education' | 'skills',
  index: number
): Promise<ApiSuccessResponse> {
  const response = await fetchWithErrorHandling(
    `${API_BASE}/resume/${section}/entries/${index}`,
    {
      method: 'DELETE',
    }
  )
  return handleResponse<ApiSuccessResponse>(response)
}

// ─── Resume version API ───────────────────────────────────────────────────────

/**
 * List all resume versions (summaries without full resume data)
 */
export async function listResumes(): Promise<ResumeVersionSummary[]> {
  const response = await fetchWithErrorHandling(`${API_BASE}/resumes`)
  return handleResponse<ResumeVersionSummary[]>(response)
}

/**
 * Get a single resume version by ID (includes full resume_data)
 */
export async function getResumeVersion(id: number): Promise<ResumeVersion> {
  const response = await fetchWithErrorHandling(`${API_BASE}/resumes/${id}`)
  return handleResponse<ResumeVersion>(response)
}

/**
 * Get the default resume version
 */
export async function getDefaultResume(): Promise<ResumeVersion> {
  const response = await fetchWithErrorHandling(`${API_BASE}/resumes/default`)
  return handleResponse<ResumeVersion>(response)
}

/**
 * Create a new resume version by cloning the current default
 */
export async function createResume(label: string): Promise<ResumeVersion> {
  const response = await fetchWithErrorHandling(`${API_BASE}/resumes`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ label }),
  })
  return handleResponse<ResumeVersion>(response)
}

/**
 * Delete a resume version
 */
export async function deleteResume(id: number): Promise<ApiSuccessResponse> {
  const response = await fetchWithErrorHandling(`${API_BASE}/resumes/${id}`, {
    method: 'DELETE',
  })
  return handleResponse<ApiSuccessResponse>(response)
}

/**
 * Set a resume version as the default
 */
export async function setDefaultResume(id: number): Promise<ApiSuccessResponse> {
  const response = await fetchWithErrorHandling(`${API_BASE}/resumes/${id}/default`, {
    method: 'POST',
  })
  return handleResponse<ApiSuccessResponse>(response)
}

/**
 * Update the label of a resume version
 */
export async function updateResumeLabel(id: number, label: string): Promise<ResumeVersion> {
  const response = await fetchWithErrorHandling(`${API_BASE}/resumes/${id}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ label }),
  })
  return handleResponse<ResumeVersion>(response)
}

/**
 * Update contact info for a specific resume version
 */
export async function updateVersionContact(
  versionId: number,
  data: Partial<ContactInfo>
): Promise<ApiSuccessResponse> {
  const response = await fetchWithErrorHandling(
    `${API_BASE}/resumes/${versionId}/contact`,
    {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    }
  )
  return handleResponse<ApiSuccessResponse>(response)
}

/**
 * Update summary for a specific resume version
 */
export async function updateVersionSummary(
  versionId: number,
  text: string
): Promise<ApiSuccessResponse> {
  const response = await fetchWithErrorHandling(
    `${API_BASE}/resumes/${versionId}/summary`,
    {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text }),
    }
  )
  return handleResponse<ApiSuccessResponse>(response)
}

/**
 * Add an entry to a version-scoped section
 */
export async function addVersionEntry(
  versionId: number,
  section: string,
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  data: any
): Promise<ApiSuccessResponse> {
  const response = await fetchWithErrorHandling(
    `${API_BASE}/resumes/${versionId}/${section}/entries`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    }
  )
  return handleResponse<ApiSuccessResponse>(response)
}

/**
 * Update an entry in a version-scoped section
 */
export async function updateVersionEntry(
  versionId: number,
  section: string,
  index: number,
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  data: any
): Promise<ApiSuccessResponse> {
  const response = await fetchWithErrorHandling(
    `${API_BASE}/resumes/${versionId}/${section}/entries/${index}`,
    {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    }
  )
  return handleResponse<ApiSuccessResponse>(response)
}

/**
 * Remove an entry from a version-scoped section
 */
export async function removeVersionEntry(
  versionId: number,
  section: string,
  index: number
): Promise<ApiSuccessResponse> {
  const response = await fetchWithErrorHandling(
    `${API_BASE}/resumes/${versionId}/${section}/entries/${index}`,
    { method: 'DELETE' }
  )
  return handleResponse<ApiSuccessResponse>(response)
}

// ─── Application API ──────────────────────────────────────────────────────────

/**
 * List applications with optional status filter and search query
 */
export async function listApplications(
  status?: string,
  q?: string
): Promise<Application[]> {
  const params = new URLSearchParams()
  if (status) params.set('status', status)
  if (q) params.set('q', q)
  const query = params.toString() ? `?${params.toString()}` : ''
  const response = await fetchWithErrorHandling(`${API_BASE}/applications${query}`)
  return handleResponse<Application[]>(response)
}

/**
 * Get a single application by ID
 */
export async function getApplication(id: number): Promise<Application> {
  const response = await fetchWithErrorHandling(`${API_BASE}/applications/${id}`)
  return handleResponse<Application>(response)
}

/**
 * Create a new application
 */
export async function createApplication(
  data: Partial<Application>
): Promise<Application> {
  const response = await fetchWithErrorHandling(`${API_BASE}/applications`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  })
  return handleResponse<Application>(response)
}

/**
 * Update an existing application
 */
export async function updateApplication(
  id: number,
  data: Partial<Application>
): Promise<Application> {
  const response = await fetchWithErrorHandling(`${API_BASE}/applications/${id}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  })
  return handleResponse<Application>(response)
}

/**
 * Delete an application
 */
export async function deleteApplication(id: number): Promise<ApiSuccessResponse> {
  const response = await fetchWithErrorHandling(`${API_BASE}/applications/${id}`, {
    method: 'DELETE',
  })
  return handleResponse<ApiSuccessResponse>(response)
}

// ─── Application contacts API ─────────────────────────────────────────────────

/**
 * List contacts for an application
 */
export async function listContacts(appId: number): Promise<ApplicationContact[]> {
  const response = await fetchWithErrorHandling(
    `${API_BASE}/applications/${appId}/contacts`
  )
  return handleResponse<ApplicationContact[]>(response)
}

/**
 * Add a contact to an application
 */
export async function addContact(
  appId: number,
  data: Partial<ApplicationContact>
): Promise<ApplicationContact> {
  const response = await fetchWithErrorHandling(
    `${API_BASE}/applications/${appId}/contacts`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    }
  )
  return handleResponse<ApplicationContact>(response)
}

/**
 * Update a contact for an application
 */
export async function updateAppContact(
  appId: number,
  contactId: number,
  data: Partial<ApplicationContact>
): Promise<ApplicationContact> {
  const response = await fetchWithErrorHandling(
    `${API_BASE}/applications/${appId}/contacts/${contactId}`,
    {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    }
  )
  return handleResponse<ApplicationContact>(response)
}

/**
 * Remove a contact from an application
 */
export async function removeContact(
  appId: number,
  contactId: number
): Promise<ApiSuccessResponse> {
  const response = await fetchWithErrorHandling(
    `${API_BASE}/applications/${appId}/contacts/${contactId}`,
    { method: 'DELETE' }
  )
  return handleResponse<ApiSuccessResponse>(response)
}

// ─── Communications API ───────────────────────────────────────────────────────

/**
 * List communications for an application
 */
export async function listCommunications(appId: number): Promise<Communication[]> {
  const response = await fetchWithErrorHandling(
    `${API_BASE}/applications/${appId}/communications`
  )
  return handleResponse<Communication[]>(response)
}

/**
 * Add a communication to an application
 */
export async function addCommunication(
  appId: number,
  data: Partial<Communication>
): Promise<Communication> {
  const response = await fetchWithErrorHandling(
    `${API_BASE}/applications/${appId}/communications`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    }
  )
  return handleResponse<Communication>(response)
}

/**
 * Update a communication for an application
 */
export async function updateCommunication(
  appId: number,
  commId: number,
  data: Partial<Communication>
): Promise<Communication> {
  const response = await fetchWithErrorHandling(
    `${API_BASE}/applications/${appId}/communications/${commId}`,
    {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    }
  )
  return handleResponse<Communication>(response)
}

/**
 * Remove a communication from an application
 */
export async function removeCommunication(
  appId: number,
  commId: number
): Promise<ApiSuccessResponse> {
  const response = await fetchWithErrorHandling(
    `${API_BASE}/applications/${appId}/communications/${commId}`,
    { method: 'DELETE' }
  )
  return handleResponse<ApiSuccessResponse>(response)
}

// ─── Accomplishments API ──────────────────────────────────────────────────────

/**
 * List accomplishments as summaries with optional tag filter and text search
 */
export async function listAccomplishments(
  tag?: string,
  q?: string
): Promise<AccomplishmentSummary[]> {
  const params = new URLSearchParams()
  if (tag) params.set('tag', tag)
  if (q) params.set('q', q)
  const query = params.toString() ? `?${params.toString()}` : ''
  const response = await fetchWithErrorHandling(`${API_BASE}/accomplishments${query}`)
  return handleResponse<AccomplishmentSummary[]>(response)
}

/**
 * Get a single accomplishment by ID (includes full STAR fields)
 */
export async function getAccomplishment(id: number): Promise<Accomplishment> {
  const response = await fetchWithErrorHandling(`${API_BASE}/accomplishments/${id}`)
  return handleResponse<Accomplishment>(response)
}

/**
 * Create a new accomplishment
 */
export async function createAccomplishment(
  data: Partial<Accomplishment>
): Promise<Accomplishment> {
  const response = await fetchWithErrorHandling(`${API_BASE}/accomplishments`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  })
  return handleResponse<Accomplishment>(response)
}

/**
 * Update an accomplishment (partial update — only provided fields change)
 */
export async function updateAccomplishment(
  id: number,
  data: Partial<Accomplishment>
): Promise<Accomplishment> {
  const response = await fetchWithErrorHandling(`${API_BASE}/accomplishments/${id}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  })
  return handleResponse<Accomplishment>(response)
}

/**
 * Delete an accomplishment by ID
 */
export async function deleteAccomplishment(id: number): Promise<ApiSuccessResponse> {
  const response = await fetchWithErrorHandling(`${API_BASE}/accomplishments/${id}`, {
    method: 'DELETE',
  })
  return handleResponse<ApiSuccessResponse>(response)
}

/**
 * Get a sorted list of all unique tags used across accomplishments (for autocomplete)
 */
export async function listAccomplishmentTags(): Promise<string[]> {
  const response = await fetchWithErrorHandling(`${API_BASE}/accomplishments/tags`)
  return handleResponse<string[]>(response)
}
