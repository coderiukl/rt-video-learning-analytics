import React, { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { courseApi } from '../../api/client'
import EmptyState from '../../components/common/EmptyState'
import { CourseCardSkeleton } from '../../components/common/LoadingSkeleton'
import { BookOpen, GraduationCap } from 'lucide-react'
import { ENROLLMENT_STATUS_LABELS, ENROLLMENT_STATUS_BADGE } from '../../utils/helpers'

export default function MyCoursesPage() {
  const [courses, setCourses] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    courseApi.myCourses()
      .then(res => setCourses(res.data?.results || res.data || []))
      .catch(() => setCourses([]))
      .finally(() => setLoading(false))
  }, [])

  return (
    <div>
      <div className="page-header">
        <h1>Khóa học của tôi</h1>
        <p>Các khóa học bạn đã đăng ký</p>
      </div>

      {loading ? (
        <div className="grid-3">
          {Array.from({ length: 4 }).map((_, i) => <CourseCardSkeleton key={i} />)}
        </div>
      ) : courses.length === 0 ? (
        <EmptyState
          icon={GraduationCap}
          title="Chưa có khóa học nào"
          description="Bạn chưa đăng ký khóa học nào. Hãy khám phá và đăng ký ngay!"
          action={<Link to="/courses" className="btn btn-primary"><BookOpen size={16} />Khám phá khóa học</Link>}
        />
      ) : (
        <div className="grid-3">
          {courses.map(enrollment => {
            const course = enrollment.course || enrollment
            const progress = Math.round(Number(enrollment.course_progress_percent || 0))
            return (
              <Link
                key={enrollment.id || course.course_id}
                to={`/courses/${course.course_id}/learn`}
                style={{ textDecoration: 'none' }}
              >
                <div
                  className="card"
                  style={{ padding: 0, overflow: 'hidden', transition: 'transform 0.2s, border-color 0.2s', cursor: 'pointer' }}
                  onMouseEnter={e => { e.currentTarget.style.transform = 'translateY(-2px)'; e.currentTarget.style.borderColor = 'var(--accent)' }}
                  onMouseLeave={e => { e.currentTarget.style.transform = 'translateY(0)'; e.currentTarget.style.borderColor = 'var(--border)' }}
                >
                  <div style={{
                    height: 140,
                    background: course.image_course ? `url(${course.image_course}) center/cover` : 'var(--bg-elevated)',
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                    borderBottom: '1px solid var(--border)',
                  }}>
                    {!course.image_course && <BookOpen size={32} color="var(--text-muted)" />}
                  </div>
                  <div style={{ padding: 18 }}>
                    <h3 style={{ fontSize: 14, fontWeight: 600, marginBottom: 10, lineHeight: 1.4 }}>
                      {course.course_name}
                    </h3>
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 12 }}>
                      {enrollment.status && (
                        <span className={`badge ${ENROLLMENT_STATUS_BADGE[enrollment.status] || 'badge-gray'}`}>
                          {ENROLLMENT_STATUS_LABELS[enrollment.status] || enrollment.status}
                        </span>
                      )}
                    </div>
                    {/* Progress bar placeholder */}
                    <div style={{ marginTop: 8 }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 12, color: 'var(--text-muted)', marginBottom: 6 }}>
                        <span>Tiến độ</span>
                        <span>{progress}%</span>
                      </div>
                      <div style={{ height: 4, background: 'var(--bg-elevated)', borderRadius: 2, overflow: 'hidden' }}>
                        <div style={{
                          height: '100%',
                          width: `${progress}%`,
                          background: 'var(--accent)',
                          borderRadius: 2,
                          transition: 'width 0.5s',
                        }} />
                      </div>
                    </div>
                  </div>
                </div>
              </Link>
            )
          })}
        </div>
      )}
    </div>
  )
}
