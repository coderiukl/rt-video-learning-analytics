import React, { useEffect, useState } from 'react'
import { courseApi, instructorManageApi } from '../../api/client'

const card = { background: 'var(--bg-surface)', border: '1px solid var(--border)', borderRadius: 16, padding: 20, marginBottom: 20 }

export default function InstructorStudentsPage() {
  const [dashboard, setDashboard] = useState(null)
  const [students, setStudents] = useState([])
  const [courses, setCourses] = useState([])
  const [courseId, setCourseId] = useState('')

  const load = async () => {
    const [d, s, c] = await Promise.all([
      instructorManageApi.dashboard(), instructorManageApi.students(courseId ? { course_id: courseId } : undefined), courseApi.instructorCourses(),
    ])
    setDashboard(d.data)
    setStudents(s.data || [])
    setCourses(c.data?.results || c.data || [])
  }

  useEffect(() => { load() }, [courseId])

  const notify = async (id) => {
    await instructorManageApi.notifyAtRisk(id, { message: 'Bạn đang chậm tiến độ. Hãy quay lại học hôm nay nhé!' })
    alert('Đã gửi thông báo')
  }

  return <div>
    <h1 style={{ marginBottom: 20 }}>Học viên & tiến độ</h1>
    {dashboard && <div className="grid-4" style={{ marginBottom: 20 }}>
      <div style={card}><b>{dashboard.total_courses}</b><p>Khóa học</p></div>
      <div style={card}><b>{dashboard.total_students}</b><p>Học viên</p></div>
      <div style={card}><b>{Math.round(dashboard.avg_progress || 0)}%</b><p>Tiến độ TB</p></div>
      <div style={card}><b>{dashboard.completed_enrollments}</b><p>Hoàn thành</p></div>
    </div>}

    <section style={card}>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 16 }}>
        <h2>Danh sách học viên</h2>
        <select className="form-input" style={{ maxWidth: 260 }} value={courseId} onChange={e => setCourseId(e.target.value)}>
          <option value="">Tất cả khóa</option>
          {courses.map(c => <option key={c.course_id} value={c.course_id}>{c.course_name}</option>)}
        </select>
      </div>
      <div style={{ display: 'grid', gap: 10 }}>
        {students.map(e => <div key={e.id} style={{ border: '1px solid var(--border)', borderRadius: 12, padding: 14, display: 'flex', justifyContent: 'space-between', gap: 16 }}>
          <div><b>{e.student_name}</b><p style={{ color: 'var(--text-muted)' }}>{e.student_email} · {e.course_name}</p><p>Tiến độ: {Math.round(e.course_progress_percent || 0)}% · Video: {e.videos_completed}</p></div>
          <button className="btn btn-primary btn-sm" onClick={() => notify(e.id)}>Nhắc học</button>
        </div>)}
        {!students.length && <p style={{ color: 'var(--text-muted)' }}>Chưa có học viên.</p>}
      </div>
    </section>
  </div>
}
