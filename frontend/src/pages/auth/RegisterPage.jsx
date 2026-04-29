import React, { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../../context/AuthContext'
import FormField from '../../components/forms/FormField'
import { BookOpen } from 'lucide-react'
import { getFieldError } from '../../utils/helpers'

export default function RegisterPage() {
  const [form, setForm] = useState({ email: '', full_name: '', password: '' })
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [success, setSuccess] = useState(false)
  const { register } = useAuth()
  const navigate = useNavigate()

  const handleChange = (e) => setForm({ ...form, [e.target.name]: e.target.value })

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError(null)
    try {
      await register(form)
      setSuccess(true)
      setTimeout(() => navigate('/login'), 2000)
    } catch (err) {
      setError(err.response?.data || { detail: 'Registration failed. Please try again.' })
    } finally {
      setLoading(false)
    }
  }

  if (success) {
    return (
      <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <div style={{ textAlign: 'center' }}>
          <div style={{ fontSize: 48, marginBottom: 16 }}>✅</div>
          <h2 style={{ fontSize: 20, marginBottom: 8 }}>Đăng ký thành công!</h2>
          <p style={{ color: 'var(--text-secondary)' }}>Đang chuyển đến trang đăng nhập...</p>
        </div>
      </div>
    )
  }

  return (
    <div style={{
      minHeight: '100vh',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      padding: 24,
    }}>
      <div style={{ width: '100%', maxWidth: 440 }}>
        <div style={{ textAlign: 'center', marginBottom: 32 }}>
          <div style={{
            width: 52, height: 52, background: 'var(--accent)',
            borderRadius: 16, display: 'flex', alignItems: 'center',
            justifyContent: 'center', margin: '0 auto 16px',
          }}>
            <BookOpen size={26} color="#fff" />
          </div>
          <h1 style={{ fontSize: 24, fontWeight: 700, marginBottom: 6 }}>Tạo tài khoản</h1>
          <p style={{ color: 'var(--text-secondary)', fontSize: 14 }}>Bắt đầu hành trình học tập</p>
        </div>

        <div className="card">
          {(error?.detail || error?.error || error?.non_field_errors?.[0]) && (
            <div style={{
              padding: '12px 16px', background: 'rgba(239,68,68,0.1)',
              border: '1px solid rgba(239,68,68,0.3)', borderRadius: 'var(--radius-md)',
              color: 'var(--error)', fontSize: 14, marginBottom: 20,
            }}>
              {error.detail || error.error || error.non_field_errors?.[0]}
            </div>
          )}

          <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: 18 }}>
            <FormField label="Họ và tên" name="full_name" value={form.full_name}
              onChange={handleChange} placeholder="Nguyễn Văn A" required
              error={getFieldError(error, 'full_name')} />

            <FormField label="Email" name="email" type="email" value={form.email}
              onChange={handleChange} placeholder="you@example.com" required
              error={getFieldError(error, 'email')} />

            <FormField label="Mật khẩu" name="password" type="password" value={form.password}
              onChange={handleChange} placeholder="Tối thiểu 8 ký tự" required
              error={getFieldError(error, 'password')} />

            <button type="submit" className="btn btn-primary btn-lg"
              disabled={loading} style={{ width: '100%', justifyContent: 'center', marginTop: 4 }}>
              {loading ? <span className="spinner" /> : 'Đăng ký'}
            </button>
          </form>
        </div>

        <p style={{ textAlign: 'center', marginTop: 20, fontSize: 14, color: 'var(--text-secondary)' }}>
          Đã có tài khoản? <Link to="/login" style={{ fontWeight: 600 }}>Đăng nhập</Link>
        </p>
      </div>
    </div>
  )
}
