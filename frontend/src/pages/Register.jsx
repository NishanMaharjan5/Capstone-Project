import { useState } from 'react'
import { Link, Navigate, useNavigate } from 'react-router-dom'
import { useAuth } from '../auth/AuthContext'
import { useGoogleIdentity } from '../auth/useGoogleIdentity'
import { registerWithGoogleCredential } from '../api/auth'

export default function Register() {
  const { isAuthenticated, register, acceptAuthResponse } = useAuth()
  const navigate = useNavigate()
  const { promptGoogle } = useGoogleIdentity()
  const [form, setForm] = useState({ name: '', email: '', password: '' })
  const [error, setError] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [isGoogleSubmitting, setIsGoogleSubmitting] = useState(false)

  if (isAuthenticated) {
    return <Navigate to="/" replace />
  }

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
      await register(form)
      navigate('/', { replace: true })
    } catch (err) {
      setError(err.message || 'Registration failed')
    } finally {
      setIsSubmitting(false)
    }
  }

  function handleGoogleSignup() {
    if (!form.name.trim()) {
      setError('Please enter your name above before signing up with Google.')
      return
    }

    setError('')
    setIsGoogleSubmitting(true)

    promptGoogle(async (credential) => {
      try {
        const data = await registerWithGoogleCredential(credential, form.name)
        acceptAuthResponse(data)
        navigate('/', { replace: true })
      } catch (err) {
        setError(err.message || 'Google sign up failed')
      } finally {
        setIsGoogleSubmitting(false)
      }
    }).catch((err) => {
      setError(err.message || 'Google sign up failed')
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
          <p className="eyebrow">Create account</p>
          <h1>Register</h1>
        </div>

        {error ? <div className="alert error">{error}</div> : null}

        <label>
          Name
          <input
            name="name"
            value={form.name}
            onChange={updateField}
            autoComplete="name"
            required
          />
        </label>

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
            autoComplete="new-password"
            minLength={6}
            required
          />
        </label>

        <button className="primary-button" type="submit" disabled={isSubmitting}>
          {isSubmitting ? 'Creating...' : 'Create account'}
        </button>

        <button
          type="button"
          className="secondary-button"
          onClick={handleGoogleSignup}
          disabled={isGoogleSubmitting}
        >
          {isGoogleSubmitting ? 'Continuing...' : 'Sign up with Google'}
        </button>

        <div className="form-links">
          <span>
            Already registered? <Link to="/login">Sign in</Link>
          </span>
        </div>
      </form>
    </section>
  )
}