import { useEffect, useState } from 'react'

export default function Login({ onLogin, loading, users }) {
  const [form, setForm] = useState({
    username: users[0]?.username || '',
    password: users[0]?.password || '',
  })
  const [error, setError] = useState('')

  useEffect(() => {
    if (users.length === 0) {
      return
    }
    setForm((prev) => {
      if (prev.username) {
        return prev
      }
      return {
        username: users[0].username,
        password: '',
      }
    })
  }, [users])

  const onChange = (field, value) => {
    setForm((prev) => ({ ...prev, [field]: value }))
  }

  const onSubmit = async (event) => {
    event.preventDefault()
    try {
      await onLogin(form)
      setError('')
    } catch (loginError) {
      setError(loginError?.message || 'Login failed')
    }
  }

  return (
    <main className="auth-shell">
      <section className="auth-card">
        <p className="eyebrow">UPI Payment Authorization Guard</p>
        <h1>Login</h1>
        <p className="muted">Sign in to continue with secure payments and live risk checks.</p>
        <div className="seeded-users">
          <p className="muted">Available Users (Loaded from Database)</p>
          {users.map((entry) => (
            <div key={entry.id} className="seeded-user-row">
              <span>{entry.name}</span>
              <span>{entry.username} / {entry.password}</span>
              <span>Port {entry.port}</span>
              <span>OTP {entry.otpEnabled ? 'ON' : 'OFF'}</span>
            </div>
          ))}
        </div>

        <form className="auth-form" onSubmit={onSubmit}>
          <label>
            Username
            <input
              value={form.username}
              onChange={(e) => onChange('username', e.target.value)}
              placeholder="Enter username"
              required
            />
          </label>
          <label>
            Password
            <input
              type="password"
              value={form.password}
              onChange={(e) => onChange('password', e.target.value)}
              placeholder="Enter password"
              required
            />
          </label>
          <button type="submit" className="btn btn-primary" disabled={loading}>
            {loading ? 'Signing in...' : 'Sign In'}
          </button>
        </form>
        {error ? <p className="otp-error">{error}</p> : null}
      </section>
    </main>
  )
}
