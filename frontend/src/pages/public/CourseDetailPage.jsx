import React, { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { courseApi, videoApi, analyticsApi, studentExtrasApi, discussionApi, reportApi } from '../../api/client'
import { useAuth } from '../../context/AuthContext'
import {
  AlertCircle, BarChart2, BookOpen, CheckCircle, Globe, User, Video, Sparkles
} from 'lucide-react'
import { LANGUAGE_LABELS, LEVEL_LABELS, STATUS_BADGE, STATUS_LABELS } from '../../utils/helpers'

export default function CourseDetailPage() {
  const { id } = useParams()
  const { user } = useAuth()
  const navigate = useNavigate()
  const [course, setCourse] = useState(null)
  const [loading, setLoading] = useState(true)
  const [enrolling, setEnrolling] = useState(false)
  const [enrollMsg, setEnrollMsg] = useState(null)
  const [videos, setVideos] = useState([])
  const [videoLoading, setVideoLoading] = useState(false)
  const [recommendations, setRecommendations] = useState([])
  const [recommendationsLoading, setRecommendationsLoading] = useState(false)
  const [reviews, setReviews] = useState([])
  const [reviewForm, setReviewForm] = useState({ rating: 5, comment: '' })
  const [discussions, setDiscussions] = useState([])
  const [discussionText, setDiscussionText] = useState('')

  useEffect(() => {
    courseApi.get(id)
      .then(res => setCourse(res.data))
      .catch(() => navigate('/courses'))
      .finally(() => setLoading(false))

    setRecommendationsLoading(true)
    analyticsApi.courseRecommendations(id)
      .then(res => setRecommendations(res.data?.recommendations || []))
      .catch(() => setRecommendations([]))
      .finally(() => setRecommendationsLoading(false))

    studentExtrasApi.reviews(id).then(res => setReviews(res.data || [])).catch(() => setReviews([]))
    discussionApi.list(id).then(res => setDiscussions(res.data || [])).catch(() => setDiscussions([]))
  }, [id, navigate])

  useEffect(() => {
    if (!course?.is_enrolled) {
      setVideos([])
      return
    }

    setVideoLoading(true)
    videoApi.list(id)
      .then(res => setVideos(res.data || []))
      .catch(() => setVideos([]))
      .finally(() => setVideoLoading(false))
  }, [course?.is_enrolled, id])

  const handleEnroll = async () => {
    if (!user) return navigate('/login')
    setEnrolling(true)
    setEnrollMsg(null)
    try {
      await courseApi.enroll(id)
      setCourse(prev => ({ ...prev, is_enrolled: true, enrollment_status: 'active' }))
      videoApi.list(id).then(res => setVideos(res.data || [])).catch(() => setVideos([]))
      setEnrollMsg({ type: 'success', text: 'Đăng ký khóa học thành công.' })
    } catch (err) {
      const message = err.response?.data?.error || err.response?.data?.detail || 'Không thể đăng ký khóa học.'
      const alreadyEnrolled = message.toLowerCase().includes('đã đăng ký')
      if (alreadyEnrolled) {
        setCourse(prev => ({ ...prev, is_enrolled: true, enrollment_status: 'active' }))
        setEnrollMsg(null)
      } else {
        setEnrollMsg({ type: 'error', text: message })
      }
    } finally {
      setEnrolling(false)
    }
  }

  const handleStartLearning = () => {
    navigate(`/courses/${id}/learn`)
  }

  const saveReview = async (e) => {
    e.preventDefault()
    await studentExtrasApi.saveReview(id, { rating: Number(reviewForm.rating), comment: reviewForm.comment })
    const res = await studentExtrasApi.reviews(id)
    setReviews(res.data || [])
    setReviewForm({ rating: 5, comment: '' })
  }

  const addDiscussion = async (e) => {
    e.preventDefault()
    if (!discussionText.trim()) return
    await discussionApi.create(id, { content: discussionText })
    const res = await discussionApi.list(id)
    setDiscussions(res.data || [])
    setDiscussionText('')
  }

  const addWishlist = async () => {
    if (!user) return navigate('/login')
    await studentExtrasApi.addWishlist(id)
    setEnrollMsg({ type: 'success', text: 'Đã thêm vào wishlist.' })
  }

  const reportCourse = async () => {
    if (!user) return navigate('/login')
    const reason = window.prompt('Lý do báo cáo khóa học?')
    if (!reason) return
    await reportApi.create({ target_type: 'course', target_id: String(id), reason })
    setEnrollMsg({ type: 'success', text: 'Đã gửi báo cáo.' })
  }

  if (loading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', paddingTop: 64 }}>
        <div className="spinner" style={{ width: 36, height: 36 }} />
      </div>
    )
  }

  if (!course) return null

  return (
    <div style={{ maxWidth: 900, margin: '0 auto' }}>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 340px', gap: 28, alignItems: 'start' }}>
        <div>
          <div style={{ marginBottom: 12 }}>
            {course.category_name && (
              <span className="badge badge-blue" style={{ marginBottom: 12 }}>{course.category_name}</span>
            )}
          </div>
          <h1 style={{ fontSize: 26, fontWeight: 700, lineHeight: 1.3, marginBottom: 16 }}>
            {course.course_name}
          </h1>

          <div style={{ display: 'flex', gap: 20, flexWrap: 'wrap', marginBottom: 24, color: 'var(--text-secondary)', fontSize: 14 }}>
            <span style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
              <User size={14} />
              {course.instructor_name || 'Instructor'}
            </span>
            {course.level && (
              <span style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                <BarChart2 size={14} />
                {LEVEL_LABELS[course.level] || course.level}
              </span>
            )}
            {course.language && (
              <span style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                <Globe size={14} />
                {LANGUAGE_LABELS[course.language] || course.language}
              </span>
            )}
          </div>

          <div className="card" style={{ marginBottom: 20 }}>
            <h3 style={{ fontSize: 15, fontWeight: 600, marginBottom: 12 }}>Mô tả khóa học</h3>
            <p style={{ color: 'var(--text-secondary)', lineHeight: 1.8, whiteSpace: 'pre-line' }}>
              {course.course_describes || 'Chưa có mô tả.'}
            </p>
          </div>

          <div className="card" style={{ marginBottom: 16, opacity: 0.6, border: '1px dashed var(--border)' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 8 }}>
              <Video size={16} color="var(--text-muted)" />
              <span style={{ fontWeight: 600, fontSize: 14 }}>Nội dung khóa học</span>
              <span className="badge badge-gray" style={{ marginLeft: 'auto' }}>
                {course.is_enrolled ? 'Sẵn sàng học' : 'Đăng ký để học'}
              </span>
            </div>
            {!course.is_enrolled ? (
              <p style={{ color: 'var(--text-muted)', fontSize: 13 }}>Đăng ký khóa học để xem danh sách video và bài giảng.</p>
            ) : videoLoading ? (
              <p style={{ color: 'var(--text-muted)', fontSize: 13 }}>Đang tải danh sách bài học...</p>
            ) : videos.length === 0 ? (
              <p style={{ color: 'var(--text-muted)', fontSize: 13 }}>Giảng viên chưa xuất bản video nào cho khóa học này.</p>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 10, marginTop: 12 }}>
                {videos.map(video => (
                  <button
                    key={video.video_id}
                    onClick={() => navigate(`/courses/${id}/learn`)}
                    style={{
                      display: 'grid', gridTemplateColumns: '28px 1fr auto', alignItems: 'center', gap: 10,
                      padding: '10px 12px', borderRadius: 'var(--radius-md)', border: '1px solid var(--border)',
                      background: 'var(--bg-elevated)', color: 'var(--text-primary)', textAlign: 'left',
                    }}
                  >
                    <Video size={15} color="var(--accent)" />
                    <span style={{ fontSize: 13, fontWeight: 500, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                      {video.order}. {video.title}
                    </span>
                    {video.duration_seconds > 0 && (
                      <span style={{ color: 'var(--text-muted)', fontSize: 12 }}>
                        {Math.floor(video.duration_seconds / 60)}:{String(video.duration_seconds % 60).padStart(2, '0')}
                      </span>
                    )}
                  </button>
                ))}
              </div>
            )}
          </div>

          {(recommendationsLoading || recommendations.length > 0) && (
            <div className="card" style={{ marginBottom: 20 }}>
              <h3 style={{ fontSize: 16, fontWeight: 700, marginBottom: 16, display: 'flex', alignItems: 'center', gap: 8, color: 'var(--accent)' }}>
                <Sparkles size={18} /> Các khóa học có thể bạn sẽ thích
              </h3>
              
              {recommendationsLoading ? (
                <div style={{ padding: 20, textAlign: 'center' }}>
                  <span className="spinner" style={{ width: 24, height: 24, display: 'inline-block' }} />
                </div>
              ) : (
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(220px, 1fr))', gap: 16 }}>
                  {recommendations.map((rec) => (
                    <div 
                      key={rec.course_id}
                      onClick={() => navigate(`/courses/${rec.course_id}`)}
                      style={{
                        padding: 16,
                        borderRadius: 'var(--radius-md)',
                        background: 'var(--bg-elevated)',
                        border: '1px solid var(--border)',
                        cursor: 'pointer',
                        transition: 'all 0.2s ease',
                      }}
                      onMouseEnter={(e) => {
                        e.currentTarget.style.borderColor = 'var(--accent)'
                        e.currentTarget.style.transform = 'translateY(-2px)'
                        e.currentTarget.style.boxShadow = '0 4px 12px rgba(0,0,0,0.1)'
                      }}
                      onMouseLeave={(e) => {
                        e.currentTarget.style.borderColor = 'var(--border)'
                        e.currentTarget.style.transform = 'none'
                        e.currentTarget.style.boxShadow = 'none'
                      }}
                    >
                      <h4 style={{ fontSize: 15, fontWeight: 600, marginBottom: 8, lineHeight: 1.4, display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical', overflow: 'hidden' }}>
                        {rec.course_name}
                      </h4>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 13, color: 'var(--text-muted)' }}>
                        <User size={13} />
                        <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                          {rec.instructor_name}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          <div className="card" style={{ marginBottom: 20 }}>
            <h3 style={{ fontSize: 16, fontWeight: 700, marginBottom: 12 }}>Đánh giá</h3>
            {user && (
              <form onSubmit={saveReview} style={{ display: 'grid', gap: 8, marginBottom: 12 }}>
                <select className="form-input" value={reviewForm.rating} onChange={e => setReviewForm({ ...reviewForm, rating: e.target.value })}>
                  {[5, 4, 3, 2, 1].map(v => <option key={v} value={v}>{v} sao</option>)}
                </select>
                <textarea className="form-input" value={reviewForm.comment} onChange={e => setReviewForm({ ...reviewForm, comment: e.target.value })} placeholder="Nhận xét khóa học" />
                <button className="btn btn-primary" type="submit">Gửi đánh giá</button>
              </form>
            )}
            {reviews.map(r => <div key={r.id} style={{ padding: 10, borderBottom: '1px solid var(--border)' }}><b>{r.student_name}</b> — {r.rating} sao<p style={{ color: 'var(--text-secondary)' }}>{r.comment}</p></div>)}
            {!reviews.length && <p style={{ color: 'var(--text-muted)' }}>Chưa có đánh giá.</p>}
          </div>

          <div className="card" style={{ marginBottom: 20 }}>
            <h3 style={{ fontSize: 16, fontWeight: 700, marginBottom: 12 }}>Thảo luận</h3>
            {user && (
              <form onSubmit={addDiscussion} style={{ display: 'flex', gap: 8, marginBottom: 12 }}>
                <input className="form-input" value={discussionText} onChange={e => setDiscussionText(e.target.value)} placeholder="Đặt câu hỏi hoặc bình luận" />
                <button className="btn btn-primary" type="submit">Gửi</button>
              </form>
            )}
            {discussions.map(d => <div key={d.id} style={{ padding: 10, borderBottom: '1px solid var(--border)' }}><b>{d.user_name}</b><p style={{ color: 'var(--text-secondary)' }}>{d.content}</p></div>)}
            {!discussions.length && <p style={{ color: 'var(--text-muted)' }}>Chưa có thảo luận.</p>}
          </div>
        </div>

        <div style={{ position: 'sticky', top: 20 }}>
          <div className="card">
            <div style={{
              height: 180,
              background: course.image_course ? `url(${course.image_course}) center/cover` : 'var(--bg-elevated)',
              borderRadius: 'var(--radius-md)',
              marginBottom: 20,
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              overflow: 'hidden',
            }}>
              {!course.image_course && <BookOpen size={40} color="var(--text-muted)" />}
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: 12, marginBottom: 20 }}>
              {[
                { label: 'Cấp độ', value: LEVEL_LABELS[course.level] || course.level },
                { label: 'Ngôn ngữ', value: LANGUAGE_LABELS[course.language] || course.language },
                { label: 'Trạng thái', value: <span className={`badge ${STATUS_BADGE[course.status] || 'badge-gray'}`}>{STATUS_LABELS[course.status] || course.status}</span> },
              ].map(item => item.value && (
                <div key={item.label} style={{ display: 'flex', justifyContent: 'space-between', fontSize: 14 }}>
                  <span style={{ color: 'var(--text-secondary)' }}>{item.label}</span>
                  <span style={{ fontWeight: 500 }}>{item.value}</span>
                </div>
              ))}
            </div>

            {enrollMsg && (
              <div style={{
                padding: '10px 14px',
                background: enrollMsg.type === 'success' ? 'rgba(34,197,94,0.1)' : 'rgba(239,68,68,0.1)',
                border: `1px solid ${enrollMsg.type === 'success' ? 'rgba(34,197,94,0.3)' : 'rgba(239,68,68,0.3)'}`,
                borderRadius: 'var(--radius-md)',
                color: enrollMsg.type === 'success' ? 'var(--success)' : 'var(--error)',
                fontSize: 13,
                marginBottom: 14,
                display: 'flex',
                alignItems: 'center',
                gap: 8,
              }}>
                {enrollMsg.type === 'success' ? <CheckCircle size={14} /> : <AlertCircle size={14} />}
                {enrollMsg.text}
              </div>
            )}

            {user?.role !== 'admin' && (
              <div style={{ display: 'grid', gap: 8 }}>
                <button
                  className="btn btn-primary btn-lg"
                  style={{ width: '100%', justifyContent: 'center' }}
                  onClick={course.is_enrolled ? handleStartLearning : handleEnroll}
                  disabled={enrolling}
                >
                  {enrolling ? <span className="spinner" /> : course.is_enrolled ? 'vào học' : 'Đăng kí khóa học'}
                </button>
                <button className="btn btn-secondary" onClick={addWishlist}>Lưu wishlist</button>
                <button className="btn btn-secondary" onClick={reportCourse}>Báo cáo khóa học</button>
              </div>
            )}

            {!user && (
              <p style={{ textAlign: 'center', fontSize: 13, color: 'var(--text-muted)', marginTop: 10 }}>
                Cần đăng nhập để đăng ký
              </p>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
