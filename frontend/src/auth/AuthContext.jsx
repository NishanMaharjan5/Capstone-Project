import { createContext, useContext, useMemo, useState } from 'react'
import { clearStoredSession } from '../api/client'
import { loginUser, registerUser } from '../api/auth'

const AuthContext = createContext(null)

function readStoredUser() {
  const token = localStorage.getItem('token')
  if (!token) return null

  return {
    token,
    name: localStorage.getItem('userName') || 'User',
    email: localStorage.getItem('userEmail') || '',
  }
}

export function AuthProvider({ children }) {
  const [user, setUser] = useState(readStoredUser)

  function persistSession(data, email = '') {
    localStorage.setItem('token', data.access_token)
    localStorage.setItem('userName', data.name || 'User')
    localStorage.setItem('userEmail', email)

    const nextUser = {
      token: data.access_token,
      name: data.name || 'User',
      email,
    }
    setUser(nextUser)
    return nextUser
  }

  async function login(credentials) {
    const data = await loginUser(credentials)
    return persistSession(data, credentials.email)
  }

  async function register(details) {
    const data = await registerUser(details)
    return persistSession(data, details.email)
  }

  function acceptAuthResponse(data, email = '') {
    return persistSession(data, email)
  }

  function logout() {
    clearStoredSession()
    setUser(null)
  }

  const value = useMemo(
    () => ({
      user,
      isAuthenticated: Boolean(user?.token),
      login,
      register,
      acceptAuthResponse,
      logout,
    }),
    [user],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used inside AuthProvider')
  }
  return context
}
