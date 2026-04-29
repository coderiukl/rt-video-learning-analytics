import React, { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { courseApi, videoApi } from '../../api/client'
import FormField from '../../components/forms/FormField'
import { ArrowLeft, Film, Link as LinkIcon, Plus, Save, Trash2, Upload } from 'lucide-react'

const emptyForm = {
  title: '',
  description: '',
  video_url: '',
  duration_seconds: '',
  order: 1,
  is_preview: false,
  is_published: true,
  video_file: null,
}

function toFormData(form) {
  const data = new FormData()
  data.append('title', form.title)
  data.append('description', form.description || '')
  data.append('video_url', form.video_url || '')
  data.append('duration_seconds', form.duration_seconds || 0)
  data.append('order', form.order || 1)
  data.append('is_preview', form.is_preview ? 'true' : 'false')
  data.append('is_published', form.is_published ? 'true' : 'false')
  if (form.video_file) {
    const ext = form.video_file.name.split('.').pop() || 'mp4'
    const safeName = `lesson-${Date.now()}.${ext}`
    data.append('video_file', form.video_file, safeName)
  }
  return data
}

export default function CourseVideosPage() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [course, setCourse] = useState(null)
  const [videos, setVideos] = useState([])
  const [form, setForm] = useState(emptyForm)
  const [editing, setEditing] = useState(null)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState(null)

  const fetchData = () => {
    setLoading(true)
    Promise.all([courseApi.getManage(id), videoApi.list(id)])
      .then(([courseRes, videoRes]) => {
        setCourse(courseRes.data)
        setVideos(videoRes.data || [])
        setForm(prev => ({ ...prev, order: (videoRes.data?.length || 0) + 1 }))
      })
      .catch(() => navigate('/instructor/courses'))
      .finally(() => setLoading(false))
  }

  useEffect(fetchData, [id])

  const resetForm = () => {
    setEditing(null)
    setError(null)
    setForm({ ...emptyForm, order: videos.length + 1 })
  }

  const handleEdit = (video) => {
    setEditing(video)
    setError(null)
    setForm({
      title: video.title || '',
      description: video.description || '',
      video_url: video.video_url || '',
      duration_seconds: video.duration_seconds || '',
      order: video.order || 1,
      is_preview: Boolean(video.is_preview),
      is_published: Boolean(video.is_published),
      video_file: null,
    })
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setSaving(true)
    setError(null)
    try {
      if (editing) await videoApi.update(editing.video_id, toFormData(form))
      else await videoApi.create(id, toFormData(form))
      resetForm()
      fetchData()
    } catch (err) {
      setError(err.response?.data?.error || err.response?.data?.non_field_errors?.[0] || 'Không thể lưu video.')
    } finally {
      setSaving(false)
    }
  }

  const handleDelete = async (video) => {
    if (!window.confirm(`Xóa video "${video.title}"?`)) return
    try {
      await videoApi.delete(video.video_id)
      fetchData()
      if (editing?.video_id === video.video_id) resetForm()
    } catch (err) {
      alert(err.response?.data?.error || 'Không thể xóa video.')
    }
  }

  if (loading) {
    return <div style={{ display: 'flex', justifyContent: 'center', paddingTop: 60 }}><div className="spinner" /></div>
  }

  return (
    <div style={{ maxWidth: 1100 }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 24 }}>
        <button className="btn btn-secondary btn-sm" onClick={() => navigate('/instructor/courses')}>
          <ArrowLeft size={14} />
        </button>
        <div>
          <h1 style={{ fontSize: 22, fontWeight: 700 }}>Video khóa học</h1>
          <p style={{ color: 'var(--text-secondary)', fontSize: 14 }}>{course?.course_name}</p>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '420px 1fr', gap: 24, alignItems: 'start' }}>
        <div className="card">
          <h2 style={{ fontSize: 16, fontWeight: 700, marginBottom: 18, display: 'flex', alignItems: 'center', gap: 8 }}>
            {editing ? <Save size={16} /> : <Plus size={16} />}
            {editing ? 'Cập nhật video' : 'Thêm video mới'}
          </h2>

          {error && <p style={{ color: 'var(--error)', fontSize: 13, marginBottom: 14 }}>{error}</p>}

          <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
            <FormField label="Tiêu đề video" name="title" value={form.title}
              onChange={e => setForm({ ...form, title: e.target.value })} required />
            <FormField label="Mô tả ngắn" name="description" type="textarea" rows={3}
              value={form.description} onChange={e => setForm({ ...form, description: e.target.value })} />

            <div>
              <label style={{ display: 'block', fontSize: 13, color: 'var(--text-secondary)', marginBottom: 8 }}>
                File video
              </label>
              <label style={{
                display: 'flex', alignItems: 'center', gap: 10, padding: '12px 14px',
                borderRadius: 'var(--radius-md)', border: '1px dashed var(--border)',
                background: 'var(--bg-elevated)', color: 'var(--text-secondary)', cursor: 'pointer',
              }}>
                <Upload size={16} />
                <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                  {form.video_file?.name || 'Chọn file MP4/WebM'}
                </span>
                <input type="file" accept="video/*" hidden onChange={e => setForm({ ...form, video_file: e.target.files?.[0] || null })} />
              </label>
            </div>

            <FormField label="Hoặc URL video" name="video_url" type="url" value={form.video_url}
              onChange={e => setForm({ ...form, video_url: e.target.value })} placeholder="https://..." />

            <div className="grid-2">
              <FormField label="Thứ tự" name="order" type="number" value={form.order}
                onChange={e => setForm({ ...form, order: e.target.value })} required />
              <FormField label="Thời lượng (giây)" name="duration_seconds" type="number" value={form.duration_seconds}
                onChange={e => setForm({ ...form, duration_seconds: e.target.value })} />
            </div>

            <label style={{ display: 'flex', alignItems: 'center', gap: 8, color: 'var(--text-secondary)', fontSize: 13 }}>
              <input type="checkbox" checked={form.is_preview} onChange={e => setForm({ ...form, is_preview: e.target.checked })} />
              Cho xem thử
            </label>
            <label style={{ display: 'flex', alignItems: 'center', gap: 8, color: 'var(--text-secondary)', fontSize: 13 }}>
              <input type="checkbox" checked={form.is_published} onChange={e => setForm({ ...form, is_published: e.target.checked })} />
              Xuất bản video
            </label>

            <div style={{ display: 'flex', gap: 10 }}>
              <button className="btn btn-primary" type="submit" disabled={saving}>
                {saving ? <span className="spinner" /> : <><Save size={15} /> {editing ? 'Lưu thay đổi' : 'Thêm video'}</>}
              </button>
              {editing && <button className="btn btn-secondary" type="button" onClick={resetForm}>Hủy</button>}
            </div>
          </form>
        </div>

        <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
          <div style={{ padding: 18, borderBottom: '1px solid var(--border)', display: 'flex', justifyContent: 'space-between' }}>
            <h2 style={{ fontSize: 16, fontWeight: 700 }}>Danh sách bài học</h2>
            <span className="badge badge-gray">{videos.length} video</span>
          </div>
          {videos.length === 0 ? (
            <div style={{ padding: 36, textAlign: 'center', color: 'var(--text-muted)' }}>
              <Film size={36} style={{ marginBottom: 10 }} />
              <p>Chưa có video nào trong khóa học này.</p>
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column' }}>
              {videos.map(video => (
                <div key={video.video_id} style={{
                  display: 'grid', gridTemplateColumns: '52px 1fr auto', gap: 14, alignItems: 'center',
                  padding: '14px 18px', borderBottom: '1px solid var(--border)',
                }}>
                  <div style={{
                    width: 42, height: 42, borderRadius: 10, background: 'var(--bg-elevated)',
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                  }}>
                    {video.video_file ? <Film size={18} /> : <LinkIcon size={18} />}
                  </div>
                  <div style={{ minWidth: 0 }}>
                    <p style={{ fontWeight: 600, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                      {video.order}. {video.title}
                    </p>
                    <p style={{ color: 'var(--text-muted)', fontSize: 12 }}>
                      {video.is_published ? 'Đã xuất bản' : 'Ẩn'} {video.is_preview ? '• Xem thử' : ''}
                    </p>
                  </div>
                  <div style={{ display: 'flex', gap: 8 }}>
                    <button className="btn btn-secondary btn-sm" onClick={() => handleEdit(video)}>Sửa</button>
                    <button className="btn btn-danger btn-sm" onClick={() => handleDelete(video)}><Trash2 size={13} /></button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
