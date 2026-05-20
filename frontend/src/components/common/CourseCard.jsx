import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { BookOpen, Globe, BarChart2, User, MoreVertical, Trash2 } from 'lucide-react'
import { LEVEL_LABELS, LANGUAGE_LABELS, STATUS_LABELS, STATUS_BADGE } from '../../utils/helpers'

export default function CourseCard({ course, showActions, onEdit, onDelete, onVideos, onAnalytics, deleting, to }) {
  const navigate = useNavigate()
  const courseId = course.course_id || course.id
  const isDeleting = deleting === courseId
  const [showMenu, setShowMenu] = useState(false)

  const handleClick = () => navigate(to || `/courses/${courseId}`)

  return (
    <div
      className="card"
      style={{ padding: 0, overflow: 'visible', cursor: 'pointer', transition: 'transform 0.2s, border-color 0.2s', position: 'relative' }}
      onMouseEnter={(e) => {
        e.currentTarget.style.transform = 'translateY(-2px)'
        e.currentTarget.style.borderColor = 'var(--accent)'
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.transform = 'translateY(0)'
        e.currentTarget.style.borderColor = 'var(--border)'
      }}
    >
      {/* Image */}
      <div
        onClick={handleClick}
        style={{
          height: 160,
          background: course.image_course
            ? `url(${course.image_course}) center/cover`
            : 'var(--bg-elevated)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          borderBottom: '1px solid var(--border)',
        }}
      >
        {!course.image_course && <BookOpen size={40} color="var(--text-muted)" />}
      </div>

      {/* Content */}
      <div style={{ padding: 18 }}>
        <div onClick={handleClick}>
          {/* Category */}
          {course.category_name && (
            <p style={{ fontSize: 11, color: 'var(--accent)', fontWeight: 600, marginBottom: 6, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
              {course.category_name}
            </p>
          )}

          {/* Title */}
          <h3 style={{ fontSize: 15, fontWeight: 600, marginBottom: 10, lineHeight: 1.4,
            display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical', overflow: 'hidden'
          }}>
            {course.course_name}
          </h3>

          {/* Instructor */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 14, color: 'var(--text-secondary)', fontSize: 13 }}>
            <User size={13} />
            <span>{course.instructor_name || course.instructor?.full_name || 'Instructor'}</span>
          </div>

          {/* Badges */}
          <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', marginBottom: 14 }}>
            {course.level && (
              <span className="badge badge-blue">{LEVEL_LABELS[course.level] || course.level}</span>
            )}
            {course.language && (
              <span className="badge badge-gray">
                <Globe size={10} style={{ marginRight: 3 }} />
                {LANGUAGE_LABELS[course.language] || course.language}
              </span>
            )}
            {course.status && (
              <span className={`badge ${STATUS_BADGE[course.status] || 'badge-gray'}`}>
                {STATUS_LABELS[course.status] || course.status}
              </span>
            )}
          </div>
        </div>

        {/* Actions for instructor */}
        {showActions && (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: 6, borderTop: '1px solid var(--border)', paddingTop: 14, marginTop: 4 }}>
            <button
              className="btn btn-secondary btn-sm"
              style={{ minWidth: 0, padding: '6px 8px', whiteSpace: 'nowrap' }}
              onClick={(e) => { e.stopPropagation(); onEdit?.(course) }}
            >
              Sửa
            </button>
            {onVideos && (
              <button
                className="btn btn-secondary btn-sm"
                style={{ minWidth: 0, padding: '6px 8px', whiteSpace: 'nowrap' }}
                onClick={(e) => { e.stopPropagation(); onVideos?.(course) }}
              >
                Video
              </button>
            )}
            {onAnalytics && (
              <button
                className="btn btn-primary btn-sm"
                style={{ minWidth: 0, padding: '6px 8px', whiteSpace: 'nowrap', display: 'inline-flex', alignItems: 'center', justifyContent: 'center', gap: 4 }}
                onClick={(e) => { e.stopPropagation(); onAnalytics?.(course) }}
                title="Phân tích Machine Learning"
              >
                <BarChart2 size={14} /> ML
              </button>
            )}
            {onDelete && (
              <button
                className="btn btn-danger btn-sm"
                style={{ minWidth: 0, padding: '6px 8px', whiteSpace: 'nowrap', display: 'inline-flex', alignItems: 'center', justifyContent: 'center', gap: 4 }}
                disabled={isDeleting}
                onClick={(e) => { e.stopPropagation(); onDelete(course) }}
                title="Xóa khóa học"
              >
                <Trash2 size={14} /> {isDeleting ? 'Đang xóa...' : 'Xóa'}
              </button>
            )}
            <div style={{ position: 'relative', display: 'none' }}>
              <button
                className="btn btn-secondary btn-sm"
                onClick={(e) => { e.stopPropagation(); setShowMenu(!showMenu) }}
                title="Thêm tùy chọn"
              >
                <MoreVertical size={14} />
              </button>
              {showMenu && (
                <div style={{
                  position: 'absolute', right: 0, top: '100%', marginTop: 4,
                  background: 'var(--bg-surface)', border: '1px solid var(--border)',
                  borderRadius: 'var(--radius-md)', boxShadow: '0 4px 12px rgba(0,0,0,0.15)',
                  zIndex: 1000, minWidth: 140,
                }}>
                  <button
                    onClick={(e) => { e.stopPropagation(); onDelete?.(course); setShowMenu(false) }}
                    style={{
                      display: 'block', width: '100%', padding: '10px 14px', textAlign: 'left',
                      background: 'transparent', border: 'none', cursor: 'pointer',
                      color: 'var(--danger)', fontSize: 13, transition: 'all 0.15s',
                    }}
                    onMouseEnter={(e) => e.currentTarget.style.background = 'rgba(239, 68, 68, 0.1)'}
                    onMouseLeave={(e) => e.currentTarget.style.background = 'transparent'}
                  >
                    🗑️ Xóa khóa học
                  </button>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
