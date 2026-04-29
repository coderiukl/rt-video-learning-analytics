import React, { useEffect, useMemo, useState } from 'react'
import { adminApi, analyticsApi } from '../../api/client'
import {
  ArrowUpDown, BookOpen, CheckCircle, Clock, GraduationCap,
  Search, ShieldCheck, Users,
} from 'lucide-react'

const cellStyle = {
  padding: '12px 14px',
  borderBottom: '1px solid var(--border)',
  fontSize: 13,
  verticalAlign: 'middle',
}

const headStyle = {
  ...cellStyle,
  color: 'var(--text-secondary)',
  fontSize: 12,
  fontWeight: 600,
  textTransform: 'uppercase',
  letterSpacing: '0.03em',
  background: 'var(--bg-elevated)',
}

function StatBox({ title, value, icon: Icon, color }) {
  return (
    <div className="card" style={{ display: 'flex', alignItems: 'center', gap: 14, padding: 18 }}>
      <div style={{
        width: 42, height: 42, borderRadius: 10, background: 'var(--bg-elevated)',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        border: '1px solid var(--border)',
      }}>
        <Icon size={20} color={color} />
      </div>
      <div>
        <p style={{ color: 'var(--text-secondary)', fontSize: 12 }}>{title}</p>
        <p style={{ fontSize: 22, fontWeight: 700 }}>{value ?? 0}</p>
      </div>
    </div>
  )
}

function Toolbar({ title, search, setSearch, sort, setSort, sortOptions }) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 12, marginBottom: 14 }}>
      <h2 style={{ fontSize: 16, fontWeight: 700 }}>{title}</h2>
      <div style={{ display: 'flex', gap: 10, alignItems: 'center' }}>
        <label style={{ position: 'relative', width: 240 }}>
          <Search size={15} style={{ position: 'absolute', left: 12, top: 10, color: 'var(--text-muted)' }} />
          <input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Tìm kiếm"
            style={{
              width: '100%', padding: '9px 12px 9px 34px', borderRadius: 'var(--radius-md)',
              border: '1px solid var(--border)', background: 'var(--bg-elevated)',
              color: 'var(--text-primary)', outline: 'none',
            }}
          />
        </label>
        <label style={{ position: 'relative' }}>
          <ArrowUpDown size={14} style={{ position: 'absolute', left: 12, top: 10, color: 'var(--text-muted)' }} />
          <select
            value={sort}
            onChange={(e) => setSort(e.target.value)}
            style={{
              width: 180, padding: '9px 12px 9px 34px', borderRadius: 'var(--radius-md)',
              border: '1px solid var(--border)', background: 'var(--bg-elevated)',
              color: 'var(--text-primary)', outline: 'none',
            }}
          >
            {sortOptions.map((option) => (
              <option key={option.value} value={option.value}>{option.label}</option>
            ))}
          </select>
        </label>
      </div>
    </div>
  )
}

function EmptyRow({ colSpan }) {
  return (
    <tr>
      <td colSpan={colSpan} style={{ ...cellStyle, color: 'var(--text-muted)', textAlign: 'center', padding: 28 }}>
        Không có dữ liệu phù hợp
      </td>
    </tr>
  )
}

export default function AdminDashboardPage() {
  const [data, setData] = useState(null)
  const [behavior, setBehavior] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [userSearch, setUserSearch] = useState('')
  const [courseSearch, setCourseSearch] = useState('')
  const [userSort, setUserSort] = useState('name')
  const [courseSort, setCourseSort] = useState('-created')

  const params = useMemo(() => ({
    user_search: userSearch,
    user_sort: userSort,
    course_search: courseSearch,
    course_sort: courseSort,
  }), [userSearch, userSort, courseSearch, courseSort])

  useEffect(() => {
    setLoading(true)
    const timer = setTimeout(() => {
      Promise.all([adminApi.dashboard(params), analyticsApi.adminBehavior()])
        .then(([dashboardRes, behaviorRes]) => {
          setData(dashboardRes.data)
          setBehavior(behaviorRes.data)
          setError(null)
        })
        .catch((err) => setError(err.response?.data?.error || 'Không thể tải dữ liệu quản trị.'))
        .finally(() => setLoading(false))
    }, 250)

    return () => clearTimeout(timer)
  }, [params])

  const stats = data?.stats || {}
  const behaviorSummary = behavior?.summary || {}
  const userSortOptions = [
    { value: 'name', label: 'Tên A-Z' },
    { value: '-name', label: 'Tên Z-A' },
    { value: '-created', label: 'Mới nhất' },
    { value: 'created', label: 'Cũ nhất' },
    { value: '-courses', label: 'Nhiều khóa học' },
    { value: '-enrollments', label: 'Nhiều ghi danh' },
  ]
  const courseSortOptions = [
    { value: '-created', label: 'Mới nhất' },
    { value: 'created', label: 'Cũ nhất' },
    { value: 'name', label: 'Tên A-Z' },
    { value: '-name', label: 'Tên Z-A' },
    { value: '-students', label: 'Nhiều học viên' },
    { value: 'status', label: 'Trạng thái' },
  ]

  return (
    <div>
      <div className="page-header">
        <h1>Quản trị hệ thống</h1>
        <p>Theo dõi người dùng, giảng viên, học viên và khóa học trên LearnFlow.</p>
      </div>

      {error && (
        <div style={{
          padding: '12px 16px', background: 'rgba(239,68,68,0.1)',
          border: '1px solid rgba(239,68,68,0.3)', borderRadius: 'var(--radius-md)',
          color: 'var(--error)', marginBottom: 20,
        }}>
          {error}
        </div>
      )}

      <div className="grid-4" style={{ marginBottom: 24 }}>
        <StatBox title="Tổng người dùng" value={stats.total_users} icon={Users} color="#4f8ef7" />
        <StatBox title="Học viên" value={stats.total_students} icon={GraduationCap} color="#22c55e" />
        <StatBox title="Giảng viên" value={stats.total_instructors} icon={ShieldCheck} color="#06b6d4" />
        <StatBox title="Tổng khóa học" value={stats.total_courses} icon={BookOpen} color="#f59e0b" />
      </div>

      <div className="grid-4" style={{ marginBottom: 28 }}>
        <StatBox title="Đang chờ duyệt" value={stats.pending_instructors} icon={Clock} color="#f59e0b" />
        <StatBox title="Đã xuất bản" value={stats.published_courses} icon={CheckCircle} color="#22c55e" />
        <StatBox title="Bản nháp" value={stats.draft_courses} icon={BookOpen} color="#8b95a8" />
        <StatBox title="Lưu trữ" value={stats.archived_courses} icon={BookOpen} color="#ef4444" />
      </div>

      <div className="grid-4" style={{ marginBottom: 28 }}>
        <StatBox title="Learning events" value={behaviorSummary.event_count} icon={Clock} color="#4f8ef7" />
        <StatBox title="Skip +10s" value={behaviorSummary.skip_forward_10_count} icon={ArrowUpDown} color="#f59e0b" />
        <StatBox title="Skip -10s" value={behaviorSummary.skip_backward_10_count} icon={ArrowUpDown} color="#06b6d4" />
        <StatBox title="Note events" value={behaviorSummary.note_event_count} icon={BookOpen} color="#22c55e" />
      </div>

      {loading && !data ? (
        <div style={{ display: 'flex', justifyContent: 'center', padding: 60 }}>
          <div className="spinner" style={{ width: 32, height: 32 }} />
        </div>
      ) : (
        <>
          <div className="card" style={{ marginBottom: 24, padding: 0, overflow: 'hidden' }}>
            <div style={{ padding: 18 }}>
              <Toolbar
                title="Giảng viên"
                search={userSearch}
                setSearch={setUserSearch}
                sort={userSort}
                setSort={setUserSort}
                sortOptions={userSortOptions}
              />
            </div>
            <div style={{ overflowX: 'auto' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', minWidth: 760 }}>
                <thead>
                  <tr>
                    <th style={headStyle}>Tên</th>
                    <th style={headStyle}>Email</th>
                    <th style={headStyle}>Chuyên môn</th>
                    <th style={headStyle}>Khóa học</th>
                    <th style={headStyle}>Trạng thái</th>
                  </tr>
                </thead>
                <tbody>
                  {data?.instructors?.length ? data.instructors.map((instructor) => (
                    <tr key={instructor.user_id}>
                      <td style={cellStyle}>{instructor.full_name}</td>
                      <td style={{ ...cellStyle, color: 'var(--text-secondary)' }}>{instructor.email}</td>
                      <td style={cellStyle}>{instructor.expertise || instructor.headline || 'Chưa cập nhật'}</td>
                      <td style={cellStyle}>{instructor.course_count}</td>
                      <td style={cellStyle}>
                        <span className={`badge ${instructor.is_verified && instructor.is_active ? 'badge-green' : 'badge-yellow'}`}>
                          {instructor.is_verified && instructor.is_active ? 'Đã duyệt' : 'Chờ duyệt'}
                        </span>
                      </td>
                    </tr>
                  )) : <EmptyRow colSpan={5} />}
                </tbody>
              </table>
            </div>
          </div>

          <div className="card" style={{ marginBottom: 24, padding: 0, overflow: 'hidden' }}>
            <div style={{ padding: 18 }}>
              <h2 style={{ fontSize: 16, fontWeight: 700 }}>Học viên</h2>
            </div>
            <div style={{ overflowX: 'auto' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', minWidth: 680 }}>
                <thead>
                  <tr>
                    <th style={headStyle}>Tên</th>
                    <th style={headStyle}>Email</th>
                    <th style={headStyle}>Khóa đang học</th>
                    <th style={headStyle}>Trạng thái</th>
                  </tr>
                </thead>
                <tbody>
                  {data?.students?.length ? data.students.map((student) => (
                    <tr key={student.user_id}>
                      <td style={cellStyle}>{student.full_name}</td>
                      <td style={{ ...cellStyle, color: 'var(--text-secondary)' }}>{student.email}</td>
                      <td style={cellStyle}>{student.enrollment_count}</td>
                      <td style={cellStyle}>
                        <span className={`badge ${student.is_active ? 'badge-green' : 'badge-red'}`}>
                          {student.is_active ? 'Hoạt động' : 'Đã khóa'}
                        </span>
                      </td>
                    </tr>
                  )) : <EmptyRow colSpan={4} />}
                </tbody>
              </table>
            </div>
          </div>

          <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
            <div style={{ padding: 18 }}>
              <Toolbar
                title="Khóa học"
                search={courseSearch}
                setSearch={setCourseSearch}
                sort={courseSort}
                setSort={setCourseSort}
                sortOptions={courseSortOptions}
              />
            </div>
            <div style={{ overflowX: 'auto' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', minWidth: 820 }}>
                <thead>
                  <tr>
                    <th style={headStyle}>Khóa học</th>
                    <th style={headStyle}>Giảng viên</th>
                    <th style={headStyle}>Danh mục</th>
                    <th style={headStyle}>Học viên</th>
                    <th style={headStyle}>Trạng thái</th>
                  </tr>
                </thead>
                <tbody>
                  {data?.courses?.length ? data.courses.map((course) => (
                    <tr key={course.course_id}>
                      <td style={cellStyle}>{course.course_name}</td>
                      <td style={{ ...cellStyle, color: 'var(--text-secondary)' }}>{course.instructor_name}</td>
                      <td style={cellStyle}>{course.category_name}</td>
                      <td style={cellStyle}>{course.enrollment_count}</td>
                      <td style={cellStyle}>
                        <span className={`badge ${
                          course.status === 'published' ? 'badge-green'
                            : course.status === 'draft' ? 'badge-yellow'
                              : 'badge-gray'
                        }`}>
                          {course.status}
                        </span>
                      </td>
                    </tr>
                  )) : <EmptyRow colSpan={5} />}
                </tbody>
              </table>
            </div>
          </div>
        </>
      )}
    </div>
  )
}
