import React, { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { useAuth } from '../../context/AuthContext'
import { courseApi } from '../../api/client'
import CourseCard from '../../components/common/CourseCard'
import EmptyState from '../../components/common/EmptyState'
import { StatCardSkeleton, CourseCardSkeleton } from '../../components/common/LoadingSkeleton'
import { BookOpen, TrendingUp, Clock, Award } from 'lucide-react'

function formatStudyTime(seconds) {
  const totalSeconds = Math.max(0, Number(seconds || 0))
  const hours = Math.floor(totalSeconds / 3600)
  const minutes = Math.floor((totalSeconds % 3600) / 60)
  if (hours) return `${hours}h ${minutes}m`
  return `${minutes}m`
}

export default function StudentDashboard() {
  const { user } = useAuth()
  const [courses, setCourses] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    courseApi.myCourses()
      .then(res => setCourses(res.data?.results || res.data || []))
      .catch(() => setCourses([]))
      .finally(() => setLoading(false))
  }, [])

  const activeCourses = courses.filter(c => c.status === 'active').length
  const completedCourses = courses.filter(c => c.status === 'completed').length
  const totalProgress = courses.reduce((sum, course) => sum + Number(course.course_progress_percent || 0), 0)
  const avgProgress = courses.length ? Math.round(totalProgress / courses.length) : 0
  const totalVideosCompleted = courses.reduce((sum, course) => sum + Number(course.videos_completed || 0), 0)
  const totalWatchTime = courses.reduce((sum, course) => sum + Number(course.total_watch_time_seconds || 0), 0)
  const completionRate = courses.length ? Math.round((completedCourses / courses.length) * 100) : 0

  const stats = [
    { title: 'Khóa đã đăng ký', value: courses.length, icon: BookOpen, color: '#4f8ef7' },
    { title: 'Đang học', value: activeCourses, icon: Clock, color: '#22c55e' },
    { title: 'Hoàn thành', value: completedCourses, icon: Award, color: '#f59e0b' },
    { title: 'Tiến độ TB', value: `${avgProgress}%`, icon: TrendingUp, color: '#06b6d4' },
  ]

  return (
    <div>
      <div style={{
        background: 'linear-gradient(135deg, var(--bg-surface) 0%, var(--bg-elevated) 100%)',
        border: '1px solid var(--border)',
        borderRadius: 'var(--radius-xl)',
        padding: '28px 32px',
        marginBottom: 32,
        position: 'relative',
        overflow: 'hidden',
      }}>
        <div style={{
          position: 'absolute',
          right: -20,
          top: -20,
          width: 180,
          height: 180,
          background: 'radial-gradient(circle, rgba(79,142,247,0.12) 0%, transparent 70%)',
        }} />
        <p style={{ color: 'var(--text-secondary)', fontSize: 14, marginBottom: 6 }}>Chào mừng trở lại</p>
        <h1 style={{ fontSize: 24, fontWeight: 700, marginBottom: 12 }}>{user?.full_name}</h1>
        <Link to="/courses" className="btn btn-primary">
          <BookOpen size={16} />
          Khám phá thêm khóa học
        </Link>
      </div>

      <div className="grid-4" style={{ marginBottom: 32 }}>
        {loading
          ? Array.from({ length: 4 }).map((_, i) => <StatCardSkeleton key={i} />)
          : stats.map(stat => (
            <div key={stat.title} className="card" style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
              <div style={{
                width: 44,
                height: 44,
                borderRadius: 12,
                background: 'var(--bg-elevated)',
                border: '1px solid var(--border)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                flexShrink: 0,
              }}>
                <stat.icon size={20} color={stat.color} />
              </div>
              <div>
                <p style={{ fontSize: 12, color: 'var(--text-secondary)', marginBottom: 2 }}>{stat.title}</p>
                <p style={{ fontSize: 22, fontWeight: 700 }}>{stat.value}</p>
              </div>
            </div>
          ))
        }
      </div>

      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
        <h2 style={{ fontSize: 16, fontWeight: 600 }}>Tiếp tục học</h2>
        <Link to="/student/my-courses" style={{ fontSize: 13 }}>Xem tất cả</Link>
      </div>

      {loading ? (
        <div className="grid-3">
          {Array.from({ length: 3 }).map((_, i) => <CourseCardSkeleton key={i} />)}
        </div>
      ) : courses.length === 0 ? (
        <EmptyState
          icon={BookOpen}
          title="Chưa đăng ký khóa học nào"
          description="Hãy khám phá và đăng ký khóa học đầu tiên của bạn"
          action={<Link to="/courses" className="btn btn-primary">Khám phá khóa học</Link>}
        />
      ) : (
        <div className="grid-3">
          {courses.slice(0, 3).map(course => (
            <CourseCard
              key={course.course_id || course.id}
              course={course}
              to={`/courses/${course.course_id || course.id}/learn`}
            />
          ))}
        </div>
      )}

      <div style={{
        marginTop: 36,
        padding: 24,
        background: 'var(--bg-surface)',
        border: '1px solid var(--border)',
        borderRadius: 'var(--radius-lg)',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 8 }}>
          <TrendingUp size={18} color="#06b6d4" />
          <h3 style={{ fontSize: 14, fontWeight: 600 }}>Learning Analytics</h3>
          <span className="badge badge-blue" style={{ marginLeft: 'auto' }}>{avgProgress}% trung bình</span>
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, minmax(0, 1fr))', gap: 14, marginTop: 16 }}>
          <div style={{ padding: 14, border: '1px solid var(--border)', borderRadius: 'var(--radius-md)', background: 'var(--bg-elevated)' }}>
            <p style={{ color: 'var(--text-secondary)', fontSize: 12, marginBottom: 4 }}>Thời gian học</p>
            <p style={{ fontSize: 20, fontWeight: 700 }}>{formatStudyTime(totalWatchTime)}</p>
          </div>
          <div style={{ padding: 14, border: '1px solid var(--border)', borderRadius: 'var(--radius-md)', background: 'var(--bg-elevated)' }}>
            <p style={{ color: 'var(--text-secondary)', fontSize: 12, marginBottom: 4 }}>Video hoàn thành</p>
            <p style={{ fontSize: 20, fontWeight: 700 }}>{totalVideosCompleted}</p>
          </div>
          <div style={{ padding: 14, border: '1px solid var(--border)', borderRadius: 'var(--radius-md)', background: 'var(--bg-elevated)' }}>
            <p style={{ color: 'var(--text-secondary)', fontSize: 12, marginBottom: 4 }}>Tỷ lệ hoàn thành</p>
            <p style={{ fontSize: 20, fontWeight: 700 }}>{completionRate}%</p>
          </div>
        </div>
      </div>
    </div>
  )
}
