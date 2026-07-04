import { useState } from 'react'
import { Link } from 'react-router-dom'
import { requestPasswordOtp, verifyPasswordOtp } from '../api/auth'

export default function ForgotPassword() {
  const [step, setStep] = useState('request')
  const [form, setForm] = useState({
    email: '',
    otp: '',
    newPassword: '',
  })
  const [message, setMessage] = useState('')
  const [error, setError] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)

  function updateField(event) {
    setForm((current) => ({
      ...current,
      [event.target.name]: event.target.value,
    }))
  }

  async function requestOtp(event) {
    event.preventDefault()
    setError('')
    setMessage('')
    setIsSubmitting(true)

    try {
      const data = await requestPasswordOtp(form.email)
      setMessage(data.message || 'OTP sent if the email is registered.')
      setStep('verify')
    } catch (err) {
      setError(err.message || 'Could not request OTP')
    } finally {
      setIsSubmitting(false)
    }
  }

  async function verifyOtp(event) {
    event.preventDefault()
    setError('')
    setMessage('')
    setIsSubmitting(true)

    try {
      const data = await verifyPasswordOtp(form)
      setMessage(data.message || 'Password reset successfully.')
      setForm({ email: '', otp: '', newPassword: '' })
      setStep('request')
    } catch (err) {
      setError(err.message || 'Could not reset password')
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <section className="auth-view">
      <form
        className="auth-card"
        onSubmit={step === 'request' ? requestOtp : verifyOtp}
      >
        <div className="section-heading">
          <p className="eyebrow">Account recovery</p>
          <h1>Reset password</h1>
        </div>

        {message ? <div className="alert success">{message}</div> : null}
        {error ? <div className="alert error">{error}</div> : null}

        <label>
          Email
          <input
            name="email"
            type="email"
            value={form.email}
            onChange={updateField}
            autoComplete="email"
            disabled={step === 'verify'}
            required
          />
        </label>

        {step === 'verify' ? (
          <>
            <label>
              OTP
              <input
                name="otp"
                value={form.otp}
                onChange={updateField}
                inputMode="numeric"
                required
              />
            </label>
            <label>
              New password
              <input
                name="newPassword"
                type="password"
                value={form.newPassword}
                onChange={updateField}
                autoComplete="new-password"
                minLength={6}
                required
              />
            </label>
          </>
        ) : null}

        <button className="primary-button" type="submit" disabled={isSubmitting}>
          {step === 'request'
            ? isSubmitting
              ? 'Sending...'
              : 'Send OTP'
            : isSubmitting
              ? 'Resetting...'
              : 'Reset password'}
        </button>

        <div className="form-links">
          <Link to="/login">Back to login</Link>
        </div>
      </form>
    </section>
  )
}
