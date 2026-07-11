import { apiRequest } from './client'

export async function createTrip(payload) {
  return apiRequest('/api/trips/', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
}

export async function getActiveTrip() {
  return apiRequest('/api/trips/active')
}

export async function listTrips() {
  return apiRequest('/api/trips/')
}

export async function getTripDetail(tripId) {
  return apiRequest(`/api/trips/${tripId}`)
}

export async function endTrip(tripId) {
  return apiRequest(`/api/trips/${tripId}/end`, { method: 'POST' })
}

export async function deleteTrip(tripId, password) {
  return apiRequest(`/api/trips/${tripId}`, {
    method: 'DELETE',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ password }),
    // A wrong confirmation password is a 401 on this endpoint specifically, not
    // an expired session — must not trigger the global logout-and-redirect.
    skipAuthRedirect: true,
  })
}
