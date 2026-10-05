import { useState, type FormEvent } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../auth'
import { Bulldog } from '../components/Bulldog'

// Log in and Create account share one form.
export default function AuthForm({ mode }: { mode: 'login' | 'signup' }) {
  const { login, signup } = useAuth()
  const navigate = useNavigate()
  const [error, setError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)
  const isSignup = mode === 'signup'

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const form = new FormData(event.currentTarget)
    const field = (name: string) => String(form.get(name) ?? '')

    if (isSignup && field('password') !== field('confirm_password')) {
      setError('Passwords do not match.')
      return
    }

    setError(null)
    setSubmitting(true)
    try {
      if (isSignup) {
        await signup({
          first_name: field('first_name'),
          last_name: field('last_name'),
          email: field('email'),
          password: field('password'),
        })
      } else {
        await login(field('email'), field('password'))
      }
      navigate('/')
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Something went wrong. Please try again.')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="container section auth-page">
      <form className="auth-card" onSubmit={handleSubmit} key={mode}>
        <Bulldog size={72} mood={isSignup ? 'happy' : 'wink'} className="auth-dog" />
        <h1>{isSignup ? 'Join the pack' : 'Welcome back'}</h1>
        <p className="muted">
          {isSignup ? 'Create an account to save your chats with Dan and pick up where you left off.' : 'Log in to your Campus Customs account.'}
        </p>

        {isSignup && (
          <div className="field-row">
            <label>
              First name
              <input name="first_name" required maxLength={50} autoComplete="given-name" />
            </label>
            <label>
              Last name
              <input name="last_name" required maxLength={50} autoComplete="family-name" />
            </label>
          </div>
        )}
        <label>
          Email
          <input name="email" type="email" required autoComplete="email" />
        </label>
        <label>
          Password
          <input
            name="password"
            type="password"
            required
            minLength={isSignup ? 8 : undefined}
            maxLength={128}
            autoComplete={isSignup ? 'new-password' : 'current-password'}
          />
          {isSignup && <small className="hint">At least 8 characters.</small>}
        </label>
        {isSignup && (
          <label>
            Confirm password
            <input name="confirm_password" type="password" required maxLength={128} autoComplete="new-password" />
          </label>
        )}

        {error && (
          <p className="form-error" role="alert">
            {error}
          </p>
        )}

        <button className="btn" type="submit" disabled={submitting}>
          {submitting ? 'Please wait…' : isSignup ? 'Create account' : 'Log in'}
        </button>

        <p className="muted small">
          {isSignup ? (
            <>
              Already have an account? <Link to="/login">Log in</Link>
            </>
          ) : (
            <>
              New here? <Link to="/signup">Create an account</Link>
            </>
          )}
        </p>
      </form>
    </div>
  )
}
