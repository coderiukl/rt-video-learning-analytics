import React, { useState, useEffect } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { courseApi, categoryApi } from '../../api/client'
import FormField from '../../components/forms/FormField'
import { getFieldError } from '../../utils/helpers'
import { ArrowLeft, CheckCircle } from 'lucide-react'

export default function EditCoursePage() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [categories, setCategories] = useState([])
  const [form, setForm] = useState(null)
  const [loading, setLoading] = useState(false)
  const [fetchLoading, setFetchLoading] = useState(true)
  const [error, setError] = useState(null)
  const [success, setSuccess] = useState(false)

  const normalizeCategories = (items) => items.flatMap((category) => [
    { ...category, parent_id: category.parent_id || null },
    ...(category.subcategories || []).map((subcategory) => ({
      ...subcategory,
      parent_id: subcategory.parent_id || category.category_id,
    })),
  ])

  useEffect(() => {
    Promise.all([courseApi.getManage(id), categoryApi.list()])
      .then(([courseRes, catRes]) => {
        const c = courseRes.data
        setForm({
          course_name: c.course_name || '', course_describes: c.course_describes || '',
          language: c.language || 'vi', level: c.level || 'beginner',
          image_course: c.image_course || '', intro_video: c.intro_video || '',
          status: c.status || 'draft',
          category: c.category || '', category_sub: c.category_sub || '',
        })
        setCategories(normalizeCategories(catRes.data?.results || catRes.data || []))
      })
      .catch(() => navigate('/instructor/courses'))
      .finally(() => setFetchLoading(false))
  }, [id, navigate])

  const rootCategories = categories.filter(c => !c.parent_id)
  const subCategories = categories.filter(c => c.parent_id && String(c.parent_id) === String(form?.category))

  const handleChange = (e) => {
    const { name, value } = e.target
    setForm(prev => ({
      ...prev,
      [name]: value,
      ...(name === 'category' ? { category_sub: '' } : {}),
    }))
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true); setError(null)
    try {
      const payload = { ...form }
      if (!payload.category_sub) delete payload.category_sub
      await courseApi.update(id, payload)
      setSuccess(true)
      setTimeout(() => navigate('/instructor/courses'), 1500)
    } catch (err) {
      setError(err.response?.data)
    } finally {
      setLoading(false)
    }
  }

  if (fetchLoading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', paddingTop: 60 }}>
        <div className="spinner" style={{ width: 32, height: 32 }} />
      </div>
    )
  }

  if (success) {
    return (
      <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', paddingTop: 80 }}>
        <CheckCircle size={48} color="var(--success)" style={{ marginBottom: 16 }} />
        <h2>Cập nhật thành công!</h2>
      </div>
    )
  }

  if (!form) return null

  return (
    <div style={{ maxWidth: 720 }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 28 }}>
        <button className="btn btn-secondary btn-sm" onClick={() => navigate(-1)}>
          <ArrowLeft size={14} />
        </button>
        <div>
          <h1 style={{ fontSize: 22, fontWeight: 700 }}>Chỉnh sửa khóa học</h1>
          <p style={{ color: 'var(--text-secondary)', fontSize: 14 }}>Cập nhật thông tin khóa học</p>
        </div>
      </div>

      <div className="card">
        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: 22 }}>
          <FormField label="Tên khóa học" name="course_name" value={form.course_name}
            onChange={handleChange} required error={getFieldError(error, 'course_name')} />
          <FormField label="Mô tả" name="course_describes" type="textarea"
            value={form.course_describes} onChange={handleChange} rows={4}
            error={getFieldError(error, 'course_describes')} />
          <div className="grid-2">
            <FormField label="Ngôn ngữ" name="language" type="select" value={form.language}
              onChange={handleChange} options={[{ value: 'vi', label: 'Tiếng Việt' }, { value: 'en', label: 'English' }]} />
            <FormField label="Cấp độ" name="level" type="select" value={form.level}
              onChange={handleChange} options={[
                { value: 'beginner', label: 'Cơ bản' },
                { value: 'intermediate', label: 'Trung cấp' },
                { value: 'advanced', label: 'Nâng cao' },
              ]} />
          </div>
          <div className="grid-2">
            <FormField label="Danh mục" name="category" type="select" value={form.category}
              onChange={handleChange}
              options={rootCategories.map(c => ({ value: c.category_id, label: c.category_name }))} />
            <FormField label="Danh mục con" name="category_sub" type="select" value={form.category_sub}
              onChange={handleChange}
              options={[{ value: '', label: '— Không chọn —' }, ...subCategories.map(c => ({ value: c.category_id, label: c.category_name }))]}
              disabled={!form.category || subCategories.length === 0} />
          </div>
          <FormField label="Trạng thái" name="status" type="select" value={form.status}
            onChange={handleChange} options={[
              { value: 'draft', label: 'Bản nháp' },
              { value: 'published', label: 'Xuất bản' },
              { value: 'archived', label: 'Lưu trữ' },
            ]} />
          <FormField label="URL ảnh bìa" name="image_course" value={form.image_course}
            onChange={handleChange} type="url" />
          <FormField label="URL video giới thiệu" name="intro_video" value={form.intro_video}
            onChange={handleChange} type="url" />

          {error?.detail && <p style={{ color: 'var(--error)', fontSize: 14 }}>{error.detail}</p>}

          <div style={{ display: 'flex', gap: 12, paddingTop: 8 }}>
            <button type="button" className="btn btn-secondary" onClick={() => navigate(-1)}>Hủy</button>
            <button type="submit" className="btn btn-primary" disabled={loading}>
              {loading ? <span className="spinner" /> : 'Lưu thay đổi'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
