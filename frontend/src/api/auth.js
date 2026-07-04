import { apiRequest } from './client'

export async function loginUser({ email, password }) {
  return apiRequest('/api/auth/login', {
    method: 'POST',
    skipAuthRedirect: true,
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password }),
  })
}

export async function registerUser({ name, email, password }) {
  return apiRequest('/api/auth/register', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name, email, password }),
  })
}

export async function loginWithGoogleCredential(credential) {
  return apiRequest('/api/auth/google', {
    method: 'POST',
    skipAuthRedirect: true,
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ credential }),
  })
}

export async function registerWithGoogleCredential(credential, name) {
  return apiRequest('/api/auth/google-register', {
    method: 'POST',
    skipAuthRedirect: true,
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ credential, name }),
  })
}

export async function requestPasswordOtp(email) {
  return apiRequest('/api/auth/forgot-password', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email }),
  })
}

export async function verifyPasswordOtp({ email, otp, newPassword }) {
  return apiRequest('/api/auth/verify-otp', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      email,
      otp,
      new_password: newPassword,
    }),
  })
}
