import React, { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Save, User } from 'lucide-react'
import { authApi } from '../../api/client'
import FormField from '../../components/forms/FormField'
import { useAuth } from '../../context/AuthContext'
import { getFieldError } from '../../utils/helpers'

export default function EditProfilePage() {
  const { user, setUser } = useAuth()
  const navigate = useNavigate()
  const [form, setForm] = useState({ full_name: '', avatar_url: '' })
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [success, setSuccess] = useState(null)

  useEffect(() => {
    if (user) {
      setForm({
        full_name: user.full_name || '',
        avatar_url: user.avatar_url || '',
      })
    }
  }, [user])

  const handleChange = (e) => {
    setForm({ ...form, [e.target.name]: e.target.value })
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError(null)
    setSuccess(null)

    try {
      const res = await authApi.updateProfile({
        full_name: form.full_name.trim(),
        avatar_url: form.avatar_url.trim() || null,
      })
      setUser(res.data)
      setSuccess('Cập nhật hồ sơ thành công.')
    } catch (err) {
      setError(err.response?.data || { detail: 'Không thể cập nhật hồ sơ.' })
    } finally {
      setLoading(false)
    }
  }

  const avatarPreview = form.avatar_url || user?.avatar_url

  return (
    <div>
      <div className="page-header">
        <h1>Chỉnh sửa hồ sơ</h1>
        <p>Cập nhật tên hiển thị và ảnh đại diện của bạn.</p>
      </div>

      <div className="card" style={{ maxWidth: 720 }}>
        {success && (
          <div style={{
            padding: '12px 16px', background: 'rgba(34,197,94,0.1)',
            border: '1px solid rgba(34,197,94,0.3)', borderRadius: 'var(--radius-md)',
            color: 'var(--success)', marginBottom: 20,
          }}>
            {success}
          </div>
        )}

        {(error?.detail || error?.error) && (
          <div style={{
            padding: '12px 16px', background: 'rgba(239,68,68,0.1)',
            border: '1px solid rgba(239,68,68,0.3)', borderRadius: 'var(--radius-md)',
            color: 'var(--error)', marginBottom: 20,
          }}>
            {error.detail || error.error}
          </div>
        )}

        <div style={{ display: 'flex', alignItems: 'center', gap: 18, marginBottom: 24 }}>
          <div style={{
            width: 88, height: 88, borderRadius: 24, overflow: 'hidden',
            background: 'var(--bg-elevated)', border: '1px solid var(--border)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
          }}>
            {avatarPreview ? (
              <img src={avatarPreview} alt="Avatar" style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
            ) : (
              <User size={34} color="var(--text-muted)" />
            )}
          </div>
          <div>
            <h2 style={{ fontSize: 18, fontWeight: 700 }}>{user?.full_name || 'Người dùng'}</h2>
            <p style={{ color: 'var(--text-secondary)', fontSize: 14 }}>{user?.email}</p>
            <p style={{ color: 'var(--text-muted)', fontSize: 12, marginTop: 6 }}>Dán URL ảnh để cập nhật ảnh đại diện.</p>
          </div>
        </div>

        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: 18 }}>
          <FormField
            label="Họ và tên"
            name="full_name"
            value={form.full_name}
            onChange={handleChange}
            placeholder="Nhập họ và tên"
            required
            error={getFieldError(error, 'full_name')}
          />

          <FormField
            label="URL ảnh đại diện"
            name="avatar_url"
            type="url"
            value={form.avatar_url}
            onChange={handleChange}
            placeholder="https://example.com/avatar.jpg"
            hint="Hiện tại hệ thống lưu ảnh đại diện bằng đường dẫn URL."
            error={getFieldError(error, 'avatar_url')}
          />

          <div style={{ display: 'flex', gap: 12, justifyContent: 'flex-end', marginTop: 8 }}>
            <button type="button" className="btn btn-secondary" onClick={() => navigate(-1)}>
              Hủy
            </button>
            <button type="submit" className="btn btn-primary" disabled={loading}>
              {loading ? <span className="spinner" /> : <><Save size={16} /> Lưu thay đổi</>}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
