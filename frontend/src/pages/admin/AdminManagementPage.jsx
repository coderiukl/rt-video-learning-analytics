import React, { useEffect, useState } from 'react'
import { adminManageApi, adminApi, reportApi } from '../../api/client'

const card = { background: 'var(--bg-surface)', border: '1px solid var(--border)', borderRadius: 16, padding: 20, marginBottom: 20 }
const table = { width: '100%', borderCollapse: 'collapse', fontSize: 14 }
const thtd = { padding: '10px 8px', borderBottom: '1px solid var(--border)', textAlign: 'left' }

export default function AdminManagementPage() {
  const [users, setUsers] = useState([])
  const [courses, setCourses] = useState([])
  const [reports, setReports] = useState([])
  const [logs, setLogs] = useState([])
  const [settings, setSettings] = useState([])
  const [loading, setLoading] = useState(true)

  const load = async () => {
    setLoading(true)
    try {
      const [u, c, r, l, s] = await Promise.all([
        adminManageApi.users(), adminManageApi.courses(), reportApi.list(), adminManageApi.auditLogs(), adminManageApi.settings(),
      ])
      setUsers(u.data || [])
      setCourses(c.data || [])
      setReports(r.data || [])
      setLogs(l.data || [])
      setSettings(s.data || [])
    } finally { setLoading(false) }
  }

  useEffect(() => { load() }, [])

  const approve = async (id) => { await adminApi.approveInstructor(id); load() }
  const reject = async (id) => { await adminManageApi.rejectInstructor(id, { reason: 'Không đạt yêu cầu.' }); load() }
  const lock = async (id) => { await adminManageApi.lockUser(id); load() }
  const moderate = async (id, status) => { await adminManageApi.moderateCourse(id, { status }); load() }
  const resolveReport = async (id, status) => { await reportApi.update(id, { status }); load() }

  if (loading) return <div className="card">Đang tải quản trị...</div>

  return <div>
    <h1 style={{ marginBottom: 20 }}>Quản trị hệ thống</h1>

    <section style={card}>
      <h2 style={{ marginBottom: 12 }}>Users</h2>
      <table style={table}><thead><tr><th style={thtd}>Tên</th><th style={thtd}>Email</th><th style={thtd}>Role</th><th style={thtd}>Trạng thái</th><th style={thtd}>Thao tác</th></tr></thead><tbody>
        {users.map(u => <tr key={u.user_id}><td style={thtd}>{u.full_name}</td><td style={thtd}>{u.email}</td><td style={thtd}>{u.role}</td><td style={thtd}>{u.is_active ? 'Active' : 'Locked'} / {u.instructor_status}</td><td style={thtd}>
          {u.instructor_status === 'pending' && <><button className="btn btn-primary btn-sm" onClick={() => approve(u.user_id)}>Duyệt</button> <button className="btn btn-secondary btn-sm" onClick={() => reject(u.user_id)}>Từ chối</button> </>}
          {u.is_active && <button className="btn btn-secondary btn-sm" onClick={() => lock(u.user_id)}>Khóa</button>}
        </td></tr>)}
      </tbody></table>
    </section>

    <section style={card}>
      <h2 style={{ marginBottom: 12 }}>Course moderation</h2>
      <table style={table}><thead><tr><th style={thtd}>Khóa</th><th style={thtd}>Instructor</th><th style={thtd}>Status</th><th style={thtd}>Thao tác</th></tr></thead><tbody>
        {courses.map(c => <tr key={c.course_id}><td style={thtd}>{c.course_name}</td><td style={thtd}>{c.instructor_name}</td><td style={thtd}>{c.status}</td><td style={thtd}>
          <button className="btn btn-primary btn-sm" onClick={() => moderate(c.course_id, 'published')}>Publish</button>{' '}
          <button className="btn btn-secondary btn-sm" onClick={() => moderate(c.course_id, 'archived')}>Archive</button>
        </td></tr>)}
      </tbody></table>
    </section>

    <section style={card}>
      <h2 style={{ marginBottom: 12 }}>Reports</h2>
      {reports.map(r => <div key={r.id} style={{ padding: 12, borderBottom: '1px solid var(--border)' }}>
        <b>{r.target_type} #{r.target_id}</b> — {r.reason} <span style={{ color: 'var(--text-muted)' }}>({r.status})</span>
        <div style={{ marginTop: 8 }}><button className="btn btn-primary btn-sm" onClick={() => resolveReport(r.id, 'resolved')}>Resolve</button> <button className="btn btn-secondary btn-sm" onClick={() => resolveReport(r.id, 'dismissed')}>Dismiss</button></div>
      </div>)}
    </section>

    <section style={card}>
      <h2 style={{ marginBottom: 12 }}>Settings</h2>
      {settings.map(s => <div key={s.id}>{s.key}: <code>{JSON.stringify(s.value)}</code></div>)}
      {!settings.length && <p style={{ color: 'var(--text-muted)' }}>Chưa có cấu hình.</p>}
    </section>

    <section style={card}>
      <h2 style={{ marginBottom: 12 }}>Audit logs</h2>
      {logs.slice(0, 30).map(l => <div key={l.id} style={{ fontSize: 13, padding: 6 }}>{l.created_at} — {l.actor_name || 'system'} — {l.action} {l.target_type} {l.target_id}</div>)}
    </section>
  </div>
}
