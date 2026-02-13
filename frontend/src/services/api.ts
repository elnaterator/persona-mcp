/**
 * API client for resume backend.
 *
 * Thin wrapper around fetch API with JSON parsing and error handling.
 */

import type {
  ApiError,
  ApiSuccessResponse,
  ContactInfo,
  Education,
  Resume,
  Skill,
  WorkExperience,
} from '../types/resume'

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
 * Converts network failures into user-friendly error messages
 */
async function fetchWithErrorHandling(
  url: string,
  options?: RequestInit
): Promise<Response> {
  try {
    return await fetch(url, options)
  } catch (error) {
    // TypeError is thrown by fetch for network failures (CORS, DNS, connection refused, etc.)
    if (error instanceof TypeError) {
      throw new ApiClientError(
        'Network error: Unable to connect to server. Please check your connection and try again.',
        0,
        'Network error: Failed to fetch'
      )
    }
    // Re-throw other errors
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
