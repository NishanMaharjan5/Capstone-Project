import { createContext, useCallback, useContext, useMemo, useState } from 'react'
import { loginUser, registerUser } from '../api/auth'
import { clearStoredSession } from '../api/client'

const AuthContext = createContext(null)

function readStoredUser() {
  const token = localStorage.getItem('token')
  const name = localStorage.getItem('userName')
  const email = localStorage.getItem('userEmail')

  if (!token) return { token: null, user: null }
  return { token, user: { name, email } }
}

export function AuthProvider({ children }) {
  const [{ token, user }, setSession] = useState(readStoredUser)

  const storeSession = useCallback((data, fallbackEmail) => {
    const email = data.email || fallbackEmail || ''
    localStorage.setItem('token', data.access_token)
    localStorage.setItem('userName', data.name || '')
    localStorage.setItem('userEmail', email)
    setSession({ token: data.access_token, user: { name: data.name, email } })
  }, [])

  const login = useCallback(
    async ({ email, password }) => {
      const data = await loginUser({ email, password })
      storeSession(data, email)
      return data
    },
    [storeSession],
  )

  const register = useCallback(
    async ({ name, email, password }) => {
      const data = await registerUser({ name, email, password })
      storeSession(data, email)
      return data
    },
    [storeSession],
  )

  // Used by Google login/register flows, which already have a token response
  // in hand and just need it applied to the session.
  const acceptAuthResponse = useCallback(
    (data, fallbackEmail) => {
      storeSession(data, fallbackEmail)
    },
    [storeSession],
  )

  const logout = useCallback(() => {
    clearStoredSession()
    setSession({ token: null, user: null })
  }, [])

  const value = useMemo(
    () => ({
      isAuthenticated: Boolean(token),
      token,
      user,
      login,
      register,
      acceptAuthResponse,
      logout,
    }),
    [token, user, login, register, acceptAuthResponse, logout],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return ctx
}
