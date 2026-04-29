import React, { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { useAuth } from '../../context/AuthContext'
import { analyticsApi, courseApi } from '../../api/client'
import { StatCardSkeleton } from '../../components/common/LoadingSkeleton'
import { Activity, Archive, BookOpen, Eye, PlusCircle, TrendingUp, Users } from 'lucide-react'

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
        <p style={{ color: 'var(--text-secondary)', fontSize: 14, marginBottom: 6 }}>Instructor Dashboard</p>
        <h1 style={{ fontSize: 24, fontWeight: 700, marginBottom: 12 }}>Xin chào, {user?.full_name}</h1>
        <Link to="/instructor/courses/create" className="btn btn-primary">
          <PlusCircle size={16} /> Tạo khóa học mới
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
              title="Engagement Analytics"
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
          title="Learning events"
          value={behaviorSummary.event_count || 0}
          desc={`${behaviorSummary.student_count || 0} students - ${behaviorSummary.video_count || 0} videos`}
          color="#4f8ef7"
        />
        <MetricCard
          icon={TrendingUp}
          title="Skip +10s"
          value={behaviorSummary.skip_forward_10_count || 0}
          desc="Signals fast-forward or skipped content"
          color="#f59e0b"
        />
        <MetricCard
          icon={Activity}
          title="Skip -10s"
          value={behaviorSummary.skip_backward_10_count || 0}
          desc="Signals replay and confusing moments"
          color="#06b6d4"
        />
        <MetricCard
          icon={BookOpen}
          title="Note events"
          value={behaviorSummary.note_event_count || 0}
          desc="Created, updated, and deleted notes"
          color="#22c55e"
        />
      </div>
    </div>
  )
}
