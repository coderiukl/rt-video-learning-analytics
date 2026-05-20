import React, { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { useAuth } from '../../context/AuthContext'
import { authApi } from '../../api/client'
import FormField from '../../components/forms/FormField'
import { User, Lock, CheckCircle, GraduationCap, Edit3 } from 'lucide-react'
import { getFieldError } from '../../utils/helpers'

export default function ProfilePage() {
  const { user, setUser } = useAuth()
  const [passwordForm, setPasswordForm] = useState({ old_password: '', new_password: '', confirm_password: '' })
  const [instructorForm, setInstructorForm] = useState({ headline: '', expertise: '', profile_url: '', bio: '' })
  const [instructorSuccess, setInstructorSuccess] = useState(false)
  const [instructorError, setInstructorError] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [success, setSuccess] = useState(false)

  useEffect(() => {
    authApi.getInstructorProfile()
      .then((res) => {
        if (res.data?.profile) {
          setInstructorForm({
            headline: res.data.profile.headline || '',
            expertise: res.data.profile.expertise || '',
            profile_url: res.data.profile.profile_url || '',
            bio: res.data.profile.bio || '',
          })
        }
      })
      .catch(() => {})
  }, [])

  const handlePasswordChange = async (e) => {
    e.preventDefault()
    if (passwordForm.new_password !== passwordForm.confirm_password) {
      setError({ confirm_password: 'Mật khẩu xác nhận không khớp' })
      return
    }
    setLoading(true); setError(null); setSuccess(false)
    try {
      await authApi.changePassword({
        old_password: passwordForm.old_password,
        new_password: passwordForm.new_password,
      })
      setSuccess(true)
      setPasswordForm({ old_password: '', new_password: '', confirm_password: '' })
    } catch (err) {
      setError(err.response?.data)
    } finally {
      setLoading(false)
    }
  }

  const handleInstructorApply = async (e) => {
    e.preventDefault()
    setLoading(true); setInstructorError(null); setInstructorSuccess(false)
    try {
      await authApi.applyInstructorProfile(instructorForm)
      const meRes = await authApi.me()
      setUser(meRes.data)
      setInstructorSuccess(true)
    } catch (err) {
      setInstructorError(err.response?.data || { error: 'Không thể gửi hồ sơ giảng viên.' })
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={{ maxWidth: 640 }}>
      <div className="page-header">
        <h1>Hồ sơ cá nhân</h1>
        <p>Thông tin tài khoản của bạn</p>
      </div>

      {/* Profile info */}
      <div className="card" style={{ marginBottom: 24 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 16, marginBottom: 24 }}>
          <div style={{
            width: 64, height: 64, borderRadius: '50%',
            background: 'var(--accent-dim)', display: 'flex',
            alignItems: 'center', justifyContent: 'center',
            fontSize: 24, fontWeight: 700, color: 'var(--accent)',
            overflow: 'hidden',
          }}>
            {user?.avatar_url ? (
              <img src={user.avatar_url} alt="Avatar" style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
            ) : (
              user?.full_name?.[0]?.toUpperCase()
            )}
          </div>
          <div style={{ flex: 1 }}>
            <h2 style={{ fontSize: 18, fontWeight: 700 }}>{user?.full_name}</h2>
            <p style={{ color: 'var(--text-secondary)', fontSize: 14, textTransform: 'capitalize' }}>{user?.role}</p>
          </div>
          <Link to="/profile/edit" className="btn btn-secondary btn-sm">
            <Edit3 size={14} /> Chỉnh sửa
          </Link>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          {[
            { label: 'Email', value: user?.email, icon: User },
            { label: 'Vai trò', value: user?.role, icon: Lock },
          ].map(item => (
            <div key={item.label} style={{ display: 'flex', alignItems: 'center', gap: 12, padding: '14px 16px',
              background: 'var(--bg-elevated)', borderRadius: 'var(--radius-md)', border: '1px solid var(--border)' }}>
              <item.icon size={16} color="var(--text-muted)" />
              <div>
                <p style={{ fontSize: 12, color: 'var(--text-muted)', marginBottom: 2 }}>{item.label}</p>
                <p style={{ fontSize: 14, fontWeight: 500, textTransform: item.label === 'Vai trò' ? 'capitalize' : 'none' }}>
                  {item.value}
                </p>
              </div>
            </div>
          ))}
        </div>
      </div>

      {user?.role === 'student' && (
        <div className="card" style={{ marginBottom: 24 }}>
          <h2 style={{ fontSize: 16, fontWeight: 600, marginBottom: 10, display: 'flex', alignItems: 'center', gap: 8 }}>
            <GraduationCap size={16} /> Hồ sơ giảng viên
          </h2>

          {user?.instructor_status === 'pending' && (
            <div style={{ padding: '12px 16px', background: 'rgba(245,158,11,0.1)', border: '1px solid rgba(245,158,11,0.3)',
              borderRadius: 'var(--radius-md)', color: '#f59e0b', fontSize: 14, marginBottom: 18 }}>
              Hồ sơ của bạn đang chờ admin duyệt.
            </div>
          )}

          {instructorSuccess && (
            <div style={{ padding: '12px 16px', background: 'rgba(34,197,94,0.1)', border: '1px solid rgba(34,197,94,0.3)',
              borderRadius: 'var(--radius-md)', color: 'var(--success)', fontSize: 14, marginBottom: 18 }}>
              Đã gửi hồ sơ. Vui lòng chờ admin duyệt.
            </div>
          )}

          {(instructorError?.error || instructorError?.detail || instructorError?.non_field_errors?.[0]) && (
            <p style={{ color: 'var(--error)', fontSize: 14, marginBottom: 18 }}>
              {instructorError.error || instructorError.detail || instructorError.non_field_errors?.[0]}
            </p>
          )}

          <form onSubmit={handleInstructorApply} style={{ display: 'flex', flexDirection: 'column', gap: 18 }}>
            <FormField label="Tiêu đề chuyên môn" name="headline" value={instructorForm.headline}
              onChange={e => setInstructorForm({ ...instructorForm, headline: e.target.value })}
              placeholder="VD: Senior Python Instructor" required
              error={getFieldError(instructorError, 'headline')} />
            <FormField label="Lĩnh vực chuyên môn" name="expertise" value={instructorForm.expertise}
              onChange={e => setInstructorForm({ ...instructorForm, expertise: e.target.value })}
              placeholder="Python, Data Analysis, Machine Learning" required
              error={getFieldError(instructorError, 'expertise')} />
            <FormField label="Đường dẫn hồ sơ" name="profile_url" value={instructorForm.profile_url}
              onChange={e => setInstructorForm({ ...instructorForm, profile_url: e.target.value })}
              placeholder="ten-giang-vien-cua-ban" required
              error={getFieldError(instructorError, 'profile_url')} />
            <FormField label="Giới thiệu" name="bio" type="textarea" rows={4}
              value={instructorForm.bio}
              onChange={e => setInstructorForm({ ...instructorForm, bio: e.target.value })}
              placeholder="Kinh nghiệm giảng dạy, thành tích, định hướng khóa học..."
              error={getFieldError(instructorError, 'bio')} />

            <button type="submit" className="btn btn-primary" disabled={loading} style={{ alignSelf: 'flex-start' }}>
              {loading ? <span className="spinner" /> : user?.instructor_status === 'pending' ? 'Cập nhật hồ sơ chờ duyệt' : 'Gửi hồ sơ xét duyệt'}
            </button>
          </form>
        </div>
      )}

      {/* Change password */}
      <div className="card">
        <h2 style={{ fontSize: 16, fontWeight: 600, marginBottom: 20, display: 'flex', alignItems: 'center', gap: 8 }}>
          <Lock size={16} /> Đổi mật khẩu
        </h2>

        {success && (
          <div style={{ padding: '12px 16px', background: 'rgba(34,197,94,0.1)', border: '1px solid rgba(34,197,94,0.3)',
            borderRadius: 'var(--radius-md)', color: 'var(--success)', fontSize: 14, marginBottom: 20,
            display: 'flex', alignItems: 'center', gap: 8 }}>
            <CheckCircle size={16} /> Đổi mật khẩu thành công!
          </div>
        )}

        <form onSubmit={handlePasswordChange} style={{ display: 'flex', flexDirection: 'column', gap: 18 }}>
          <FormField label="Mật khẩu hiện tại" name="old_password" type="password"
            value={passwordForm.old_password} onChange={e => setPasswordForm({...passwordForm, old_password: e.target.value})}
            required error={getFieldError(error, 'old_password')} />
          <FormField label="Mật khẩu mới" name="new_password" type="password"
            value={passwordForm.new_password} onChange={e => setPasswordForm({...passwordForm, new_password: e.target.value})}
            required error={getFieldError(error, 'new_password')} />
          <FormField label="Xác nhận mật khẩu mới" name="confirm_password" type="password"
            value={passwordForm.confirm_password} onChange={e => setPasswordForm({...passwordForm, confirm_password: e.target.value})}
            required error={getFieldError(error, 'confirm_password')} />

          <button type="submit" className="btn btn-primary" disabled={loading} style={{ alignSelf: 'flex-start' }}>
            {loading ? <span className="spinner" /> : 'Cập nhật mật khẩu'}
          </button>
        </form>
      </div>
    </div>
  )
}
