import React, { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { courseApi, categoryApi } from '../../api/client'
import FormField from '../../components/forms/FormField'
import { getFieldError } from '../../utils/helpers'
import { ArrowLeft, CheckCircle } from 'lucide-react'

export default function CreateCoursePage() {
  const navigate = useNavigate()
  const [categories, setCategories] = useState([])
  const [form, setForm] = useState({
    course_name: '', course_describes: '', language: 'vi', level: 'beginner',
    image_course: '', intro_video: '', status: 'draft', category: '', category_sub: '',
  })
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [success, setSuccess] = useState(false)

  useEffect(() => {
    categoryApi.list()
      .then(res => setCategories(res.data?.results || res.data || []))
      .catch(() => {})
  }, [])

  const rootCategories = categories.filter(c => !c.parent_id)
  const subCategories = categories.filter(c => c.parent_id && String(c.parent_id) === String(form.category))

  const handleChange = (e) => {
    setForm({ ...form, [e.target.name]: e.target.value })
    if (e.target.name === 'category') setForm(prev => ({ ...prev, category: e.target.value, category_sub: '' }))
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true); setError(null)
    try {
      const payload = { ...form }
      if (!payload.category_sub) delete payload.category_sub
      if (!payload.image_course) delete payload.image_course
      if (!payload.intro_video) delete payload.intro_video
      await courseApi.create(payload)
      setSuccess(true)
      setTimeout(() => navigate('/instructor/courses'), 1500)
    } catch (err) {
      setError(err.response?.data || { detail: 'Không thể tạo khóa học. Vui lòng thử lại.' })
    } finally {
      setLoading(false)
    }
  }

  if (success) {
    return (
      <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', paddingTop: 80 }}>
        <CheckCircle size={48} color="var(--success)" style={{ marginBottom: 16 }} />
        <h2 style={{ fontSize: 20, marginBottom: 8 }}>Tạo khóa học thành công!</h2>
        <p style={{ color: 'var(--text-secondary)' }}>Đang chuyển đến danh sách khóa học...</p>
      </div>
    )
  }

  return (
    <div style={{ maxWidth: 720 }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 28 }}>
        <button className="btn btn-secondary btn-sm" onClick={() => navigate(-1)}>
          <ArrowLeft size={14} />
        </button>
        <div>
          <h1 style={{ fontSize: 22, fontWeight: 700 }}>Tạo khóa học mới</h1>
          <p style={{ color: 'var(--text-secondary)', fontSize: 14 }}>Điền thông tin khóa học</p>
        </div>
      </div>

      <div className="card">
        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: 22 }}>
          <FormField label="Tên khóa học" name="course_name" value={form.course_name}
            onChange={handleChange} placeholder="VD: Python cơ bản cho người mới" required
            error={getFieldError(error, 'course_name')} />

          <FormField label="Mô tả" name="course_describes" type="textarea"
            value={form.course_describes} onChange={handleChange}
            placeholder="Mô tả nội dung và mục tiêu khóa học..." rows={4}
            error={getFieldError(error, 'course_describes')} />

          <div className="grid-2">
            <FormField label="Ngôn ngữ" name="language" type="select" value={form.language}
              onChange={handleChange} options={[{ value: 'vi', label: 'Tiếng Việt' }, { value: 'en', label: 'English' }]}
              error={getFieldError(error, 'language')} />
            <FormField label="Cấp độ" name="level" type="select" value={form.level}
              onChange={handleChange} options={[
                { value: 'beginner', label: 'Cơ bản' },
                { value: 'intermediate', label: 'Trung cấp' },
                { value: 'advanced', label: 'Nâng cao' },
              ]} error={getFieldError(error, 'level')} />
          </div>

          <div className="grid-2">
            <FormField label="Danh mục" name="category" type="select" value={form.category}
              onChange={handleChange}
              options={rootCategories.map(c => ({ value: c.category_id, label: c.category_name }))}
              error={getFieldError(error, 'category')} />
            {subCategories.length > 0 && (
              <FormField label="Danh mục con" name="category_sub" type="select" value={form.category_sub}
                onChange={handleChange}
                options={subCategories.map(c => ({ value: c.category_id, label: c.category_name }))}
                error={getFieldError(error, 'category_sub')} />
            )}
          </div>

          <FormField label="Trạng thái" name="status" type="select" value={form.status}
            onChange={handleChange} options={[
              { value: 'draft', label: 'Bản nháp' },
              { value: 'published', label: 'Xuất bản' },
            ]} error={getFieldError(error, 'status')} />

          <FormField label="URL ảnh bìa" name="image_course" value={form.image_course}
            onChange={handleChange} placeholder="https://..." type="url"
            error={getFieldError(error, 'image_course')} />

          <FormField label="URL video giới thiệu" name="intro_video" value={form.intro_video}
            onChange={handleChange} placeholder="https://..." type="url"
            hint="Tính năng xem video sẽ sớm ra mắt"
            error={getFieldError(error, 'intro_video')} />

          {(error?.detail || error?.error || error?.non_field_errors?.[0]) && (
            <p style={{ color: 'var(--error)', fontSize: 14 }}>
              {error.detail || error.error || error.non_field_errors?.[0]}
            </p>
          )}

          <div style={{ display: 'flex', gap: 12, paddingTop: 8 }}>
            <button type="button" className="btn btn-secondary" onClick={() => navigate(-1)}>
              Hủy
            </button>
            <button type="submit" className="btn btn-primary" disabled={loading}>
              {loading ? <span className="spinner" /> : 'Tạo khóa học'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
