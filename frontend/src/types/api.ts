/**
 * API-level error and response types.
 */

export interface ApiValidationError {
  loc: string[]
  msg: string
  type: string
}

export interface ApiError {
  detail: string | ApiValidationError[]
}

export interface ApiSuccessResponse {
  message: string
}

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
