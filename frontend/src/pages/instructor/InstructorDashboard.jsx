import React, { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { useAuth } from '../../context/AuthContext'
import { analyticsApi, courseApi } from '../../api/client'
import { StatCardSkeleton } from '../../components/common/LoadingSkeleton'
import { Activity, Archive, BookOpen, Eye, PlusCircle, TrendingUp, Users, ArrowRight } from 'lucide-react'

function MetricCard({ icon: Icon, title, value, desc, color }) {
  return (
    <div className="card">
      <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 10 }}>
        <div style={{
          width: 40,
          height: 40,
          borderRadius: 10,
          background: 'var(--bg-elevated)',
          border: '1px solid var(--border)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
        }}>
          <Icon size={20} color={color} />
        </div>
        <div style={{ minWidth: 0 }}>
          <p style={{ fontSize: 13, color: 'var(--text-secondary)', marginBottom: 2 }}>{title}</p>
          <p style={{ fontSize: 26, fontWeight: 800, lineHeight: 1 }}>{value}</p>
        </div>
      </div>
      <p style={{ color: 'var(--text-secondary)', fontSize: 13 }}>{desc}</p>
    </div>
  )
}

export default function InstructorDashboard() {
  const { user } = useAuth()
  const [courses, setCourses] = useState([])
  const [behavior, setBehavior] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.all([courseApi.instructorCourses(), analyticsApi.instructorBehavior()])
      .then(([courseRes, behaviorRes]) => {
        setCourses(courseRes.data?.results || courseRes.data || [])
        setBehavior(behaviorRes.data)
      })
      .catch(() => {
        setCourses([])
        setBehavior(null)
      })
      .finally(() => setLoading(false))
  }, [])

  const published = courses.filter(c => c.status === 'published').length
  const drafts = courses.filter(c => c.status === 'draft').length
  const archived = courses.filter(c => c.status === 'archived').length

  const totalStudents = courses.reduce((sum, course) => sum + Number(course.total_students || 0), 0)
  const activeStudents = courses.reduce((sum, course) => sum + Number(course.active_students || 0), 0)
  const completedStudents = courses.reduce((sum, course) => sum + Number(course.completed_students || 0), 0)
  const totalProgressWeight = courses.reduce((sum, course) => {
    return sum + Number(course.avg_progress_percent || 0) * Number(course.total_students || 0)
  }, 0)
  const avgProgress = totalStudents ? Math.round(totalProgressWeight / totalStudents) : 0
  const completionRate = totalStudents ? Math.round((completedStudents / totalStudents) * 100) : 0
  const behaviorSummary = behavior?.summary || {}

  const stats = [
    { title: 'Tổng khóa học', value: courses.length, icon: BookOpen, color: '#4f8ef7' },
    { title: 'Đã xuất bản', value: published, icon: Eye, color: '#22c55e' },
    { title: 'Bản nháp', value: drafts, icon: TrendingUp, color: '#f59e0b' },
    { title: 'Đã lưu trữ', value: archived, icon: Archive, color: '#8b95a8' },
  ]

  return (
    <div>
      <div style={{
        background: 'linear-gradient(135deg, var(--bg-surface) 0%, var(--bg-elevated) 100%)',
        border: '1px solid var(--border)',
        borderRadius: 'var(--radius-xl)',
        padding: '28px 32px',
        marginBottom: 32,
      }}>
        <p style={{ color: 'var(--text-secondary)', fontSize: 14, marginBottom: 6 }}>Bảng điều khiển giảng viên</p>
        <h1 style={{ fontSize: 24, fontWeight: 700, marginBottom: 12 }}>Xin chào, {user?.full_name}</h1>
        <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
          <Link to="/instructor/courses/create" className="btn btn-primary">
            <PlusCircle size={16} /> Tạo khóa học mới
          </Link>
          <Link to="/instructor/students" className="btn btn-secondary">
            <Users size={16} /> Xem học viên
          </Link>
        </div>
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

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20 }}>
        {loading ? (
          Array.from({ length: 2 }).map((_, i) => <StatCardSkeleton key={i} />)
        ) : (
          <>
            <MetricCard
              icon={Users}
              title="Tổng học viên đăng ký"
              value={totalStudents}
              desc={`${activeStudents} đang học - ${completedStudents} hoàn thành`}
              color="#4f8ef7"
            />
            <MetricCard
              icon={Activity}
              title="Sự tham gia"
              value={`${avgProgress}%`}
              desc={`Tiến độ trung bình - ${completionRate}% hoàn thành`}
              color="#22c55e"
            />
          </>
        )}
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, minmax(0, 1fr))', gap: 20, marginTop: 20 }}>
        <MetricCard
          icon={Activity}
          title="Sự kiện học tập"
          value={behaviorSummary.event_count || 0}
          desc={`${behaviorSummary.student_count || 0} học viên - ${behaviorSummary.video_count || 0} video`}
          color="#4f8ef7"
        />
        <MetricCard
          icon={TrendingUp}
          title="Tua nhanh +10s"
          value={behaviorSummary.skip_forward_10_count || 0}
          desc="Tín hiệu tua nhanh hoặc bỏ qua nội dung"
          color="#f59e0b"
        />
        <MetricCard
          icon={Activity}
          title="Tua lùi -10s"
          value={behaviorSummary.skip_backward_10_count || 0}
          desc="Tín hiệu xem lại và những phần khó hiểu"
          color="#06b6d4"
        />
        <MetricCard
          icon={BookOpen}
          title="Sự kiện ghi chú"
          value={behaviorSummary.note_event_count || 0}
          desc="Ghi chú được tạo, cập nhật và xóa"
          color="#22c55e"
        />
      </div>

      <div style={{ marginTop: 32 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
          <h2 style={{ fontSize: 18, fontWeight: 700 }}>Khóa học gần đây</h2>
          <Link to="/instructor/courses" style={{ display: 'flex', alignItems: 'center', gap: 6, color: 'var(--accent)', textDecoration: 'none', fontSize: 14 }}>
            Xem tất cả <ArrowRight size={14} />
          </Link>
        </div>
        {courses.length === 0 ? (
          <div style={{ padding: 24, textAlign: 'center', background: 'var(--bg-elevated)', borderRadius: 'var(--radius-lg)', color: 'var(--text-muted)' }}>
            Chưa có khóa học nào. <Link to="/instructor/courses/create" style={{ color: 'var(--accent)', textDecoration: 'none' }}>Tạo khóa học đầu tiên</Link>
          </div>
        ) : (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))', gap: 16 }}>
            {courses.slice(0, 4).map(course => (
              <Link
                key={course.course_id}
                to={`/instructor/courses/${course.course_id}/videos`}
                style={{
                  padding: 16,
                  background: 'var(--bg-elevated)',
                  border: '1px solid var(--border)',
                  borderRadius: 'var(--radius-md)',
                  textDecoration: 'none',
                  color: 'inherit',
                  transition: 'all 0.2s',
                  cursor: 'pointer',
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.borderColor = 'var(--accent)'
                  e.currentTarget.style.transform = 'translateY(-2px)'
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.borderColor = 'var(--border)'
                  e.currentTarget.style.transform = 'translateY(0)'
                }}
              >
                <p style={{ fontSize: 12, color: 'var(--text-secondary)', marginBottom: 6 }}>{course.status === 'published' ? '✓ Xuất bản' : '○ Bản nháp'}</p>
                <h3 style={{ fontSize: 14, fontWeight: 600, marginBottom: 8, display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical', overflow: 'hidden' }}>
                  {course.course_name}
                </h3>
                <p style={{ fontSize: 12, color: 'var(--text-muted)' }}>
                  {course.total_students || 0} học viên
                </p>
              </Link>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
