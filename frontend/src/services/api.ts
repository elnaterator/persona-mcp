/**
 * API client for resume backend.
 *
 * Thin wrapper around fetch API with JSON parsing and error handling.
 */

import type {
  Accomplishment,
  AccomplishmentSummary,
  ApiError,
  ApiValidationError,
  ApiSuccessResponse,
  Application,
  ApplicationContact,
  Communication,
  CommunicationSearchResult,
  Contact,
  ContactInfo,
  ContactSummary,
  Education,
  GroupedLinks,
  Note,
  NoteSummary,
  ResourceRef,
  ResourceType,
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
        if (Array.isArray(errorData.detail)) {
          detail = (errorData.detail as ApiValidationError[])
            .map((e) => {
              const field = e.loc?.filter((s) => s !== 'body').slice(-1)[0]
              return field ? `${field}: ${e.msg}` : e.msg
            })
            .join('; ')
        } else {
          detail = errorData.detail
        }
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
 * Update resume contact information
 */
export async function updateResumeContact(
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
 * Update the label and/or tags of a resume version
 */
export async function updateResumeLabel(
  id: number,
  label: string,
  tags?: string[]
): Promise<ResumeVersion> {
  const body: Record<string, unknown> = { label }
  if (tags !== undefined) body.tags = tags
  const response = await fetchWithErrorHandling(`${API_BASE}/resumes/${id}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
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
 * List applications with optional status/tag filter and search query
 */
export async function listApplications(
  status?: string,
  q?: string,
  tags?: string[]
): Promise<Application[]> {
  const params = new URLSearchParams()
  if (status) params.set('status', status)
  if (q) params.set('q', q)
  if (tags && tags.length > 0) tags.forEach((t) => params.append('tag', t))
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
export async function listAppContacts(appId: number): Promise<ApplicationContact[]> {
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

// ─── Contact Communications API ───────────────────────────────────────────────

function _mapComm(raw: Record<string, unknown>): Communication {
  return {
    ...(raw as unknown as Communication),
    app_id: raw.app_id as number | null | undefined,
    contact_ref_id: raw.contact_ref_id as number | null | undefined,
    tags: (raw.tags as string[]) ?? [],
  }
}

export async function listContactCommunications(
  contactId: number
): Promise<Communication[]> {
  const response = await fetchWithErrorHandling(
    `${API_BASE}/contacts/${contactId}/communications`
  )
  const data = await handleResponse<unknown[]>(response)
  return data.map((r) => _mapComm(r as Record<string, unknown>))
}

export async function addContactCommunication(
  contactId: number,
  data: Partial<Communication>
): Promise<Communication> {
  const response = await fetchWithErrorHandling(
    `${API_BASE}/contacts/${contactId}/communications`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    }
  )
  const raw = await handleResponse<Record<string, unknown>>(response)
  return _mapComm(raw)
}

export async function updateContactCommunication(
  contactId: number,
  commId: number,
  data: Partial<Communication>
): Promise<Communication> {
  const response = await fetchWithErrorHandling(
    `${API_BASE}/contacts/${contactId}/communications/${commId}`,
    {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    }
  )
  const raw = await handleResponse<Record<string, unknown>>(response)
  return _mapComm(raw)
}

export async function removeContactCommunication(
  contactId: number,
  commId: number
): Promise<ApiSuccessResponse> {
  const response = await fetchWithErrorHandling(
    `${API_BASE}/contacts/${contactId}/communications/${commId}`,
    { method: 'DELETE' }
  )
  return handleResponse<ApiSuccessResponse>(response)
}

export async function searchCommunications(params: {
  q?: string
  tags?: string[]
  parent?: 'application' | 'contact' | 'all'
}): Promise<CommunicationSearchResult[]> {
  const qs = new URLSearchParams()
  if (params.q) qs.set('q', params.q)
  if (params.tags?.length) params.tags.forEach((t) => qs.append('tag', t))
  if (params.parent && params.parent !== 'all') qs.set('parent', params.parent)
  const response = await fetchWithErrorHandling(
    `${API_BASE}/communications${qs.toString() ? `?${qs}` : ''}`
  )
  const data = await handleResponse<Record<string, unknown>[]>(response)
  return data.map((r) => ({
    ...(_mapComm(r) as CommunicationSearchResult),
    parentType: r.parent_type as 'application' | 'contact',
    parentId: r.parent_id as number,
    parentName: r.parent_name as string,
  }))
}

// ─── Accomplishments API ──────────────────────────────────────────────────────

/**
 * List accomplishments as summaries with optional tag filter (AND logic) and text search
 */
export async function listAccomplishments(
  tags?: string[],
  q?: string
): Promise<AccomplishmentSummary[]> {
  const params = new URLSearchParams()
  if (tags && tags.length > 0) tags.forEach((t) => params.append('tag', t))
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

// ─── Notes API ─────────────────────────────────────────────────────────────────

/**
 * List notes as summaries with optional tag filter (AND logic) and text search
 */
export async function listNotes(
  tags?: string[],
  q?: string
): Promise<NoteSummary[]> {
  const params = new URLSearchParams()
  if (tags && tags.length > 0) tags.forEach((t) => params.append('tag', t))
  if (q) params.set('q', q)
  const query = params.toString() ? `?${params.toString()}` : ''
  const response = await fetchWithErrorHandling(`${API_BASE}/notes${query}`)
  return handleResponse<NoteSummary[]>(response)
}

/**
 * Get a single note by ID (includes full content)
 */
export async function getNote(id: number): Promise<Note> {
  const response = await fetchWithErrorHandling(`${API_BASE}/notes/${id}`)
  return handleResponse<Note>(response)
}

/**
 * Create a new note
 */
export async function createNote(
  data: Partial<Note>
): Promise<Note> {
  const response = await fetchWithErrorHandling(`${API_BASE}/notes`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  })
  return handleResponse<Note>(response)
}

/**
 * Update a note (partial update — only provided fields change)
 */
export async function updateNote(
  id: number,
  data: Partial<Note>
): Promise<Note> {
  const response = await fetchWithErrorHandling(`${API_BASE}/notes/${id}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  })
  return handleResponse<Note>(response)
}

/**
 * Delete a note by ID
 */
export async function deleteNote(id: number): Promise<ApiSuccessResponse> {
  const response = await fetchWithErrorHandling(`${API_BASE}/notes/${id}`, {
    method: 'DELETE',
  })
  return handleResponse<ApiSuccessResponse>(response)
}

/**
 * Get a sorted list of all unique tags used across notes (for autocomplete)
 */
export async function listNoteTags(): Promise<string[]> {
  const response = await fetchWithErrorHandling(`${API_BASE}/notes/tags`)
  return handleResponse<string[]>(response)
}

// ─── Contacts API ──────────────────────────────────────────────────────────────

/**
 * List contacts as summaries with optional tag filter (AND logic) and text search
 */
export async function listContacts(
  tags?: string[],
  q?: string
): Promise<ContactSummary[]> {
  const params = new URLSearchParams()
  if (tags && tags.length > 0) tags.forEach((t) => params.append('tag', t))
  if (q) params.set('q', q)
  const query = params.toString() ? `?${params.toString()}` : ''
  const response = await fetchWithErrorHandling(`${API_BASE}/contacts${query}`)
  return handleResponse<ContactSummary[]>(response)
}

/**
 * Get a single contact by ID (includes full notes)
 */
export async function getContact(id: number): Promise<Contact> {
  const response = await fetchWithErrorHandling(`${API_BASE}/contacts/${id}`)
  return handleResponse<Contact>(response)
}

/**
 * Create a new contact
 */
export async function createContact(data: Partial<Contact>): Promise<Contact> {
  const response = await fetchWithErrorHandling(`${API_BASE}/contacts`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  })
  return handleResponse<Contact>(response)
}

/**
 * Update a contact (partial update — only provided fields change)
 */
export async function updateContact(
  id: number,
  data: Partial<Contact>
): Promise<Contact> {
  const response = await fetchWithErrorHandling(`${API_BASE}/contacts/${id}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  })
  return handleResponse<Contact>(response)
}

/**
 * Delete a contact by ID
 */
export async function deleteContact(id: number): Promise<ApiSuccessResponse> {
  const response = await fetchWithErrorHandling(`${API_BASE}/contacts/${id}`, {
    method: 'DELETE',
  })
  return handleResponse<ApiSuccessResponse>(response)
}

/**
 * Get a sorted list of all unique tags used across contacts (for autocomplete)
 */
export async function listContactTags(): Promise<string[]> {
  const response = await fetchWithErrorHandling(`${API_BASE}/contacts/tags`)
  return handleResponse<string[]>(response)
}

// ─── Unified Tags API ──────────────────────────────────────────────────────────

/**
 * Get a sorted, deduplicated list of all tags across all resource types
 */
export async function listAllTags(): Promise<string[]> {
  const response = await fetchWithErrorHandling(`${API_BASE}/tags`)
  return handleResponse<string[]>(response)
}

/**
 * Get all unique tags used across applications
 */
export async function listApplicationTags(): Promise<string[]> {
  const response = await fetchWithErrorHandling(`${API_BASE}/applications/tags`)
  return handleResponse<string[]>(response)
}

/**
 * Get all unique tags used across resume versions
 */
export async function listResumeTags(): Promise<string[]> {
  const response = await fetchWithErrorHandling(`${API_BASE}/resumes/tags`)
  return handleResponse<string[]>(response)
}

// ─── Resource Links API ────────────────────────────────────────────────────────

function _mapRef(raw: Record<string, unknown>): ResourceRef {
  return {
    type: raw.type as ResourceType,
    id: raw.id as number,
    name: raw.name as string,
    updatedAt: raw.updated_at as string | null | undefined,
  }
}

export function mapGroupedLinks(
  raw: Record<string, unknown[]> | undefined
): GroupedLinks {
  if (!raw) return {}
  const result: GroupedLinks = {}
  for (const [type, refs] of Object.entries(raw)) {
    result[type as ResourceType] = (refs as Record<string, unknown>[]).map(_mapRef)
  }
  return result
}

export async function linkResources(
  aType: ResourceType,
  aId: number,
  bType: ResourceType,
  bId: number
): Promise<ApiSuccessResponse> {
  const response = await fetchWithErrorHandling(`${API_BASE}/links`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ a_type: aType, a_id: aId, b_type: bType, b_id: bId }),
  })
  return handleResponse<ApiSuccessResponse>(response)
}

export async function unlinkResources(
  aType: ResourceType,
  aId: number,
  bType: ResourceType,
  bId: number
): Promise<void> {
  const response = await fetchWithErrorHandling(`${API_BASE}/links`, {
    method: 'DELETE',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ a_type: aType, a_id: aId, b_type: bType, b_id: bId }),
  })
  if (!response.ok && response.status !== 204) {
    await handleResponse<void>(response)
  }
}
