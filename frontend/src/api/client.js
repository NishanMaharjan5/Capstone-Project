const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

export class ApiError extends Error {
  constructor(message, status, data) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.data = data
  }
}

export function getApiBaseUrl() {
  return API_BASE_URL
}

export async function apiRequest(path, options = {}) {
  const { skipAuthRedirect = false, ...requestOptions } = options
  const token = localStorage.getItem('token')
  const headers = new Headers(requestOptions.headers || {})

  if (token && !headers.has('Authorization')) {
    headers.set('Authorization', `Bearer ${token}`)
  }

  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...requestOptions,
    headers,
  })

  const contentType = response.headers.get('content-type') || ''
  const data = contentType.includes('application/json')
    ? await response.json()
    : await response.text()

  if (!response.ok) {
    if (response.status === 401 && !skipAuthRedirect) {
      clearStoredSession()
      window.location.assign('/login')
    }

    const message =
      typeof data === 'object' && data?.detail
        ? data.detail
        : 'Request failed'
    throw new ApiError(message, response.status, data)
  }

  return data
}

export function clearStoredSession() {
  localStorage.removeItem('token')
  localStorage.removeItem('userName')
  localStorage.removeItem('userEmail')
}
