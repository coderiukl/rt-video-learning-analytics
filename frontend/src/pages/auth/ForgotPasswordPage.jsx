import React, { useState } from 'react'
import { Link } from 'react-router-dom'
import { authApi } from '../../api/client'
import FormField from '../../components/forms/FormField'
import { BookOpen, ArrowLeft } from 'lucide-react'
import { getFieldError } from '../../utils/helpers'

// 3 bước: send-otp → verify-otp → reset
export default function ForgotPasswordPage() {
  const [step, setStep] = useState(1) // 1, 2, 3
  const [email, setEmail] = useState('')
  const [otp, setOtp] = useState('')
  const [resetToken, setResetToken] = useState('')
  const [newPassword, setNewPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [done, setDone] = useState(false)

  const handleSendOtp = async (e) => {
    e.preventDefault()
    setLoading(true); setError(null)
    try {
      await authApi.sendOtp({ email })
      setStep(2)
    } catch (err) { setError(err.response?.data) }
    finally { setLoading(false) }
  }

  const handleVerifyOtp = async (e) => {
    e.preventDefault()
    setLoading(true); setError(null)
    try {
      const res = await authApi.verifyOtp({ email, otp })
      setResetToken(res.data.reset_token)
      setStep(3)
    } catch (err) { setError(err.response?.data) }
    finally { setLoading(false) }
  }

  const handleReset = async (e) => {
    e.preventDefault()
    setLoading(true); setError(null)
    try {
      await authApi.resetPassword({ email, reset_token: resetToken, new_password: newPassword })
      setDone(true)
    } catch (err) { setError(err.response?.data) }
    finally { setLoading(false) }
  }

  const cardStyle = { width: '100%', maxWidth: 420 }
  const stepLabels = ['Nhập email', 'Xác minh OTP', 'Đặt lại mật khẩu']

  if (done) {
    return (
      <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <div style={{ textAlign: 'center' }}>
          <div style={{ fontSize: 48, marginBottom: 16 }}>🔓</div>
          <h2 style={{ fontSize: 20, marginBottom: 8 }}>Đặt lại mật khẩu thành công!</h2>
          <Link to="/login" className="btn btn-primary" style={{ marginTop: 16 }}>Đăng nhập ngay</Link>
        </div>
      </div>
    )
  }

  return (
    <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 24 }}>
      <div style={cardStyle}>
        <div style={{ textAlign: 'center', marginBottom: 32 }}>
          <div style={{
            width: 52, height: 52, background: 'var(--accent)', borderRadius: 16,
            display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 16px',
          }}>
            <BookOpen size={26} color="#fff" />
          </div>
          <h1 style={{ fontSize: 22, fontWeight: 700, marginBottom: 6 }}>Quên mật khẩu</h1>
          {/* Step indicator */}
          <div style={{ display: 'flex', justifyContent: 'center', gap: 8, marginTop: 16 }}>
            {[1,2,3].map(s => (
              <div key={s} style={{
                width: s === step ? 24 : 8, height: 8, borderRadius: 4,
                background: s <= step ? 'var(--accent)' : 'var(--border)',
                transition: 'all 0.3s',
              }} />
            ))}
          </div>
          <p style={{ color: 'var(--text-secondary)', fontSize: 13, marginTop: 10 }}>
            Bước {step}/3 — {stepLabels[step - 1]}
          </p>
        </div>

        <div className="card">
          {(error?.detail || error?.error || error?.non_field_errors?.[0]) && (
            <div style={{ padding: '12px 16px', background: 'rgba(239,68,68,0.1)', border: '1px solid rgba(239,68,68,0.3)',
              borderRadius: 'var(--radius-md)', color: 'var(--error)', fontSize: 14, marginBottom: 20 }}>
              {error.detail || error.error || error.non_field_errors?.[0]}
            </div>
          )}

          {step === 1 && (
            <form onSubmit={handleSendOtp} style={{ display: 'flex', flexDirection: 'column', gap: 18 }}>
              <FormField label="Email đăng ký" name="email" type="email" value={email}
                onChange={e => setEmail(e.target.value)} placeholder="you@example.com" required
                error={getFieldError(error, 'email')} />
              <button type="submit" className="btn btn-primary" disabled={loading}
                style={{ width: '100%', justifyContent: 'center' }}>
                {loading ? <span className="spinner" /> : 'Gửi mã OTP'}
              </button>
            </form>
          )}

          {step === 2 && (
            <form onSubmit={handleVerifyOtp} style={{ display: 'flex', flexDirection: 'column', gap: 18 }}>
              <p style={{ color: 'var(--text-secondary)', fontSize: 14 }}>
                Mã OTP đã được gửi đến <strong style={{ color: 'var(--text-primary)' }}>{email}</strong>
              </p>
              <FormField label="Mã OTP" name="otp" value={otp}
                onChange={e => setOtp(e.target.value)} placeholder="Nhập mã OTP" required
                error={getFieldError(error, 'otp')} />
              <button type="submit" className="btn btn-primary" disabled={loading}
                style={{ width: '100%', justifyContent: 'center' }}>
                {loading ? <span className="spinner" /> : 'Xác minh'}
              </button>
            </form>
          )}

          {step === 3 && (
            <form onSubmit={handleReset} style={{ display: 'flex', flexDirection: 'column', gap: 18 }}>
              <FormField label="Mật khẩu mới" name="new_password" type="password"
                value={newPassword} onChange={e => setNewPassword(e.target.value)}
                placeholder="Tối thiểu 8 ký tự" required
                error={getFieldError(error, 'new_password')} />
              <button type="submit" className="btn btn-primary" disabled={loading}
                style={{ width: '100%', justifyContent: 'center' }}>
                {loading ? <span className="spinner" /> : 'Đặt lại mật khẩu'}
              </button>
            </form>
          )}
        </div>

        <p style={{ textAlign: 'center', marginTop: 20, fontSize: 14 }}>
          <Link to="/login" style={{ color: 'var(--text-secondary)', display: 'inline-flex', alignItems: 'center', gap: 6 }}>
            <ArrowLeft size={14} /> Quay lại đăng nhập
          </Link>
        </p>
      </div>
    </div>
  )
}
