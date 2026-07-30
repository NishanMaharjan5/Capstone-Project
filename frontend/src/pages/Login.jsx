import { useState } from 'react'
import { Link, Navigate, useLocation, useNavigate } from 'react-router-dom'
import { useAuth } from '../auth/AuthContext'
import { useGoogleIdentity } from '../auth/useGoogleIdentity'
import { loginWithGoogleCredential } from '../api/auth'

export default function Login() {
  const { isAuthenticated, login, acceptAuthResponse } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const { promptGoogle } = useGoogleIdentity()
  const [form, setForm] = useState({ email: '', password: '' })
  const [error, setError] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [isGoogleSubmitting, setIsGoogleSubmitting] = useState(false)

  if (isAuthenticated) {
    return <Navigate to="/" replace />
  }

  const nextPath = location.state?.from?.pathname || '/'

  function updateField(event) {
    setForm((current) => ({
      ...current,
      [event.target.name]: event.target.value,
    }))
  }

  async function handleSubmit(event) {
    event.preventDefault()
    setError('')
    setIsSubmitting(true)

    try {
      await login(form)
      navigate(nextPath, { replace: true })
    } catch (err) {
      setError(err.message || 'Login failed')
    } finally {
      setIsSubmitting(false)
    }
  }

  function handleGoogleLogin() {
    setError('')
    setIsGoogleSubmitting(true)

    promptGoogle(async (credential) => {
      try {
        const data = await loginWithGoogleCredential(credential)
        acceptAuthResponse(data)
        navigate(nextPath, { replace: true })
      } catch (err) {
        setError(err.message || 'Google login failed')
      } finally {
        setIsGoogleSubmitting(false)
      }
    }).catch((err) => {
      setError(err.message || 'Google login failed')
      setIsGoogleSubmitting(false)
    })
  }

  return (
    <section className="auth-view">
      <form className="auth-card" onSubmit={handleSubmit}>
        <div className="auth-brand">
          <span className="auth-brand-mark" />
          <span className="auth-brand-name">Centa</span>
        </div>

        <div className="section-heading">
          <p className="eyebrow">Welcome back</p>
          <h1>Sign in</h1>
        </div>

        {error ? <div className="alert error">{error}</div> : null}

        <label>
          Email
          <input
            name="email"
            type="email"
            value={form.email}
            onChange={updateField}
            autoComplete="email"
            required
          />
        </label>

        <label>
          Password
          <input
            name="password"
            type="password"
            value={form.password}
            onChange={updateField}
            autoComplete="current-password"
            required
          />
        </label>

        <button className="primary-button" type="submit" disabled={isSubmitting}>
          {isSubmitting ? 'Signing in...' : 'Sign in'}
        </button>

        <button
          type="button"
          className="secondary-button"
          onClick={handleGoogleLogin}
          disabled={isGoogleSubmitting}
        >
          {isGoogleSubmitting ? 'Continuing...' : 'Continue with Google'}
        </button>

        <div className="form-links">
          <Link to="/forgot-password">Forgot password?</Link>
          <span>
            New here? <Link to="/register">Create account</Link>
          </span>
        </div>
      </form>
    </section>
  )
}