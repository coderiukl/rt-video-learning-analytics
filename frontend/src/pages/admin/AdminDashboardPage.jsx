
import React, { useEffect, useMemo, useState } from 'react'
import { adminApi, adminManageApi, categoryApi, reportApi } from '../../api/client'
import { BookOpen, Check, FileText, History, Search, Settings, ShieldCheck, Tag, Users, Eye, X, Link as LinkIcon, Award, Calendar } from 'lucide-react'

const s = {
  title: 'Qu\u1ea3n tr\u1ecb h\u1ec7 th\u1ed1ng', subtitle: 'Qu\u1ea3n l\u00fd ng\u01b0\u1eddi d\u00f9ng, gi\u1ea3ng vi\u00ean, kh\u00f3a h\u1ecdc, b\u00e1o c\u00e1o v\u00e0 c\u1ea5u h\u00ecnh.',
  overview: 'T\u1ed5ng quan', users: 'Ng\u01b0\u1eddi d\u00f9ng', instructors: 'Gi\u1ea3ng vi\u00ean', courses: 'Kh\u00f3a h\u1ecdc', categories: 'Danh m\u1ee5c', reports: 'B\u00e1o c\u00e1o', logs: 'Nh\u1eadt k\u00fd', settings: 'C\u1ea5u h\u00ecnh',
  totalUsers: 'T\u1ed5ng ng\u01b0\u1eddi d\u00f9ng', students: 'H\u1ecdc vi\u00ean', totalCourses: 'T\u1ed5ng kh\u00f3a h\u1ecdc', todo: 'Vi\u1ec7c c\u1ea7n x\u1eed l\u00fd', pendingTeachers: 'Gi\u1ea3ng vi\u00ean ch\u1edd duy\u1ec7t', openReports: 'B\u00e1o c\u00e1o \u0111ang m\u1edf', draftCourses: 'Kh\u00f3a h\u1ecdc b\u1ea3n nh\u00e1p',
  search: 'T\u00ecm ki\u1ebfm', name: 'T\u00ean', email: 'Email', role: 'Role', status: 'Tr\u1ea1ng th\u00e1i', actions: 'Thao t\u00e1c', active: 'Ho\u1ea1t \u0111\u1ed9ng', locked: '\u0110\u00e3 kh\u00f3a', reset: 'Reset m\u1eadt kh\u1ea9u', lock: 'Kh\u00f3a', approve: 'Duy\u1ec7t', reject: 'T\u1eeb ch\u1ed1i', teacher: 'Gi\u1ea3ng vi\u00ean', category: 'Danh m\u1ee5c', course: 'Kh\u00f3a h\u1ecdc', reporter: 'Ng\u01b0\u1eddi b\u00e1o c\u00e1o', target: '\u0110\u1ed1i t\u01b0\u1ee3ng', reason: 'L\u00fd do', addSetting: 'Th\u00eam c\u1ea5u h\u00ecnh', systemSettings: 'C\u1ea5u h\u00ecnh h\u1ec7 th\u1ed1ng', auditLog: 'Nh\u1eadt k\u00fd thao t\u00e1c', noData: 'Kh\u00f4ng c\u00f3 d\u1eef li\u1ec7u',
  rejectReason: 'L\u00fd do t\u1eeb ch\u1ed1i?', rejectDefault: 'H\u1ed3 s\u01a1 ch\u01b0a \u0111\u1ea1t y\u00eau c\u1ea7u.', confirmLock: 'Kh\u00f3a t\u00e0i kho\u1ea3n n\u00e0y?', newPassword: 'M\u1eadt kh\u1ea9u m\u1edbi (t\u1ed1i thi\u1ec3u 8 k\u00fd t\u1ef1)', resetDone: '\u0110\u00e3 reset m\u1eadt kh\u1ea9u.', settingKey: 'Key c\u1ea5u h\u00ecnh', settingJson: 'Value JSON', childCats: 'danh m\u1ee5c con', createCat: 'T\u1ea1o danh m\u1ee5c', edit: 'S\u1eeda', delete: 'X\u00f3a', catName: 'T\u00ean danh m\u1ee5c', parentId: 'ID danh m\u1ee5c cha (b\u1ecf tr\u1ed1ng n\u1ebfu l\u00e0 danh m\u1ee5c g\u1ed1c)', confirmDeleteCat: 'X\u00f3a danh m\u1ee5c n\u00e0y?', cancel: 'H\u1ee7y', save: 'L\u01b0u', rootCat: 'Danh m\u1ee5c g\u1ed1c' 
}

const cell = { padding: '12px 14px', borderBottom: '1px solid var(--border)', fontSize: 13, verticalAlign: 'middle' }
const head = { ...cell, color: 'var(--text-secondary)', fontSize: 12, fontWeight: 700, textTransform: 'uppercase', background: 'var(--bg-elevated)', textAlign: 'left' }
const box = { background: 'var(--bg-surface)', border: '1px solid var(--border)', borderRadius: 'var(--radius-xl)', overflow: 'hidden', marginBottom: 24 }

function Btn({ children, onClick, variant = 'secondary', disabled, type = 'button' }) { return <button type={type} className={`btn btn-${variant} btn-sm`} disabled={disabled} onClick={onClick}>{children}</button> }
function Table({ headers, children }) { return <div style={box}><table style={{ width: '100%', borderCollapse: 'collapse' }}><thead><tr>{headers.map(h => <th key={h} style={head}>{h}</th>)}</tr></thead><tbody>{children}</tbody></table></div> }
function Section({ title, children, right }) { return <section style={box}><div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: 18, borderBottom: '1px solid var(--border)' }}><h2 style={{ fontSize: 17, fontWeight: 800 }}>{title}</h2>{right}</div>{children}</section> }
function Stat({ icon: Icon, label, value, color }) { return <div className="card" style={{ display: 'flex', gap: 14, alignItems: 'center', padding: 18 }}><div style={{ width: 42, height: 42, borderRadius: 10, display: 'flex', alignItems: 'center', justifyContent: 'center', background: 'var(--bg-elevated)', border: '1px solid var(--border)' }}><Icon size={20} color={color} /></div><div><p style={{ color: 'var(--text-secondary)', fontSize: 12 }}>{label}</p><p style={{ fontSize: 24, fontWeight: 800 }}>{value ?? 0}</p></div></div> }

export default function AdminDashboardPage() {
  const [tab, setTab] = useState('overview')
  const [dashboard, setDashboard] = useState({})
  const [users, setUsers] = useState([])
  const [courses, setCourses] = useState([])
  const [reports, setReports] = useState([])
  const [logs, setLogs] = useState([])
  const [settingsRows, setSettingsRows] = useState([])
  const [categories, setCategories] = useState([])
  const [search, setSearch] = useState('')
  const [categoryForm, setCategoryForm] = useState(null)
  const [loading, setLoading] = useState(true)
  const [viewingInstructor, setViewingInstructor] = useState(null)

  const load = async () => {
    setLoading(true)
    try {
      const [dash, userRes, courseRes, reportRes, logRes, settingRes, catRes] = await Promise.all([adminApi.dashboard(), adminManageApi.users(), adminManageApi.courses(), reportApi.list(), adminManageApi.auditLogs(), adminManageApi.settings(), categoryApi.list()])
      setDashboard(dash.data || {})
      setUsers(userRes.data || [])
      setCourses(courseRes.data || [])
      setReports(reportRes.data || [])
      setLogs(logRes.data || [])
      setSettingsRows(settingRes.data || [])
      setCategories(catRes.data?.results || catRes.data || [])
    } finally { setLoading(false) }
  }
  useEffect(() => { load() }, [])

  const stats = dashboard?.stats || {}
  const filteredUsers = useMemo(() => users.filter(u => `${u.full_name} ${u.email} ${u.role}`.toLowerCase().includes(search.toLowerCase())), [users, search])
  const filteredCourses = useMemo(() => courses.filter(c => `${c.course_name} ${c.instructor_name} ${c.status}`.toLowerCase().includes(search.toLowerCase())), [courses, search])
  const instructors = filteredUsers.filter(u => u.role === 'instructor' || u.instructor_status !== 'none')

  const approveInstructor = async id => { await adminApi.approveInstructor(id); await load() }
  const rejectInstructor = async id => { const reason = window.prompt(s.rejectReason, s.rejectDefault); if (reason !== null) { await adminManageApi.rejectInstructor(id, { reason }); await load() } }
  const lockUser = async id => { if (window.confirm(s.confirmLock)) { await adminManageApi.lockUser(id); await load() } }
  const resetPassword = async id => { const pwd = window.prompt(s.newPassword); if (pwd) { await adminManageApi.resetPassword(id, { new_password: pwd }); alert(s.resetDone) } }
  const moderateCourse = async (id, status) => { await adminManageApi.moderateCourse(id, { status }); await load() }
  const updateReport = async (id, status) => { await reportApi.update(id, { status }); await load() }
  const saveSetting = async () => { const key = window.prompt(s.settingKey); if (!key) return; const raw = window.prompt(s.settingJson, '{}'); if (raw === null) return; await adminManageApi.saveSetting({ key, value: JSON.parse(raw || '{}') }); await load() }
  const openCreateCategory = () => setCategoryForm({ mode: 'create', category_id: null, category_name: '', parent: '' })
  const openEditCategory = cat => setCategoryForm({ mode: 'edit', category_id: cat.category_id, category_name: cat.category_name, parent: cat.parent_id || '' })
  const saveCategory = async form => { const payload = { category_name: form.category_name, parent: form.parent ? Number(form.parent) : null }; if (form.mode === 'edit') await categoryApi.update(form.category_id, payload); else await categoryApi.create(payload); setCategoryForm(null); await load() }
  const deleteCategory = async id => { if (window.confirm(s.confirmDeleteCat)) { await categoryApi.delete(id); await load() } }

  const tabs = [[ 'overview', s.overview, ShieldCheck ], [ 'users', s.users, Users ], [ 'instructors', s.instructors, Check ], [ 'courses', s.courses, BookOpen ], [ 'categories', s.categories, Tag ], [ 'reports', s.reports, FileText ], [ 'logs', s.logs, History ], [ 'settings', s.settings, Settings ]]
  if (loading) return <div className="card">Loading...</div>

  return <div>
    <div style={{ marginBottom: 24 }}><h1 style={{ fontSize: 26, fontWeight: 900, marginBottom: 8 }}>{s.title}</h1><p style={{ color: 'var(--text-secondary)' }}>{s.subtitle}</p></div>
    <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', paddingBottom: 14, borderBottom: '1px solid var(--border)', marginBottom: 24 }}>{tabs.map(([id, label, Icon]) => <button key={id} className={`btn btn-${tab === id ? 'primary' : 'secondary'} btn-sm`} onClick={() => setTab(id)}><Icon size={15} /> {label}</button>)}</div>
    {tab !== 'overview' && <div style={{ position: 'relative', maxWidth: 340, marginBottom: 18 }}><Search size={15} style={{ position: 'absolute', left: 12, top: 11, color: 'var(--text-muted)' }} /><input className="form-input" style={{ paddingLeft: 36 }} value={search} onChange={e => setSearch(e.target.value)} placeholder={s.search} /></div>}
    {tab === 'overview' && <><div className="grid-4" style={{ marginBottom: 24 }}><Stat icon={Users} label={s.totalUsers} value={stats.total_users} color="#4f8ef7" /><Stat icon={Users} label={s.students} value={stats.total_students} color="#22c55e" /><Stat icon={ShieldCheck} label={s.instructors} value={stats.total_instructors} color="#06b6d4" /><Stat icon={BookOpen} label={s.totalCourses} value={stats.total_courses} color="#f59e0b" /></div><Section title={s.todo}><div style={{ padding: 18, display: 'grid', gap: 12 }}><p>{s.pendingTeachers}: <b>{stats.pending_instructors || 0}</b></p><p>{s.openReports}: <b>{reports.filter(r => r.status === 'open').length}</b></p><p>{s.draftCourses}: <b>{stats.draft_courses || 0}</b></p></div></Section></>}
    {tab === 'users' && <UserTable users={filteredUsers} onLock={lockUser} onReset={resetPassword} />}
    {tab === 'instructors' && <InstructorTable users={instructors} onApprove={approveInstructor} onReject={rejectInstructor} onLock={lockUser} onView={setViewingInstructor} />}
    {viewingInstructor && <InstructorProfileModal user={viewingInstructor} onClose={() => setViewingInstructor(null)} onApprove={async id => { await approveInstructor(id); setViewingInstructor(null) }} onReject={async id => { await rejectInstructor(id); setViewingInstructor(null) }} />}
    {tab === 'courses' && <CourseTable courses={filteredCourses} onModerate={moderateCourse} />}
    {tab === 'categories' && <CategoryList categories={categories} form={categoryForm} setForm={setCategoryForm} onCreate={openCreateCategory} onEdit={openEditCategory} onSave={saveCategory} onDelete={deleteCategory} />}
    {tab === 'reports' && <ReportTable reports={reports} onUpdate={updateReport} />}
    {tab === 'logs' && <LogList logs={logs} />}
    {tab === 'settings' && <SettingsList rows={settingsRows} onAdd={saveSetting} />}
  </div>
}

function UserTable({ users, onLock, onReset }) { return <Table headers={[s.name, s.email, s.role, s.status, s.actions]}>{users.map(u => <tr key={u.user_id}><td style={cell}>{u.full_name}</td><td style={cell}>{u.email}</td><td style={cell}>{u.role}</td><td style={cell}>{u.is_active ? s.active : s.locked}</td><td style={cell}><Btn onClick={() => onReset(u.user_id)}>{s.reset}</Btn> {u.is_active && <Btn onClick={() => onLock(u.user_id)}>{s.lock}</Btn>}</td></tr>)}</Table> }
function InstructorTable({ users, onApprove, onReject, onLock, onView }) {
  return <Table headers={[s.name, s.email, s.status, s.courses, s.actions]}>{users.map(u => {
    const hasProfile = !!u.instructor_profile
    return <tr key={u.user_id}>
      <td style={cell}>{u.full_name}</td>
      <td style={cell}>{u.email}</td>
      <td style={cell}><StatusBadge status={u.instructor_status} /></td>
      <td style={cell}>{u.courses_count || 0}</td>
      <td style={cell}>
        {hasProfile && <Btn onClick={() => onView(u)}><Eye size={13} /> Xem hồ sơ</Btn>}{' '}
        {u.instructor_status === 'pending' && <><Btn variant="primary" onClick={() => onApprove(u.user_id)}>{s.approve}</Btn> <Btn onClick={() => onReject(u.user_id)}>{s.reject}</Btn> </>}
        {u.is_active && <Btn onClick={() => onLock(u.user_id)}>{s.lock}</Btn>}
      </td>
    </tr>
  })}</Table>
}

function StatusBadge({ status }) {
  const map = {
    pending: { bg: 'rgba(245,158,11,0.15)', color: '#f59e0b', label: 'Chờ duyệt' },
    approved: { bg: 'rgba(34,197,94,0.15)', color: '#22c55e', label: 'Đã duyệt' },
    none: { bg: 'var(--bg-elevated)', color: 'var(--text-muted)', label: '—' },
  }
  const cfg = map[status] || map.none
  return <span style={{ padding: '4px 10px', borderRadius: 12, fontSize: 12, fontWeight: 600, background: cfg.bg, color: cfg.color }}>{cfg.label}</span>
}

function InstructorProfileModal({ user, onClose, onApprove, onReject }) {
  const p = user.instructor_profile || {}
  const isPending = user.instructor_status === 'pending'
  return <div onClick={onClose} style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.6)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000, padding: 20, backdropFilter: 'blur(4px)' }}>
    <div onClick={e => e.stopPropagation()} style={{ background: 'var(--bg-surface)', border: '1px solid var(--border)', borderRadius: 16, maxWidth: 640, width: '100%', maxHeight: '90vh', overflow: 'auto', boxShadow: '0 20px 60px rgba(0,0,0,0.4)' }}>
      <div style={{ padding: '20px 24px', borderBottom: '1px solid var(--border)', display: 'flex', alignItems: 'center', justifyContent: 'space-between', position: 'sticky', top: 0, background: 'var(--bg-surface)', zIndex: 1 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <ShieldCheck size={20} color="var(--accent)" />
          <h3 style={{ fontSize: 17, fontWeight: 800 }}>Hồ sơ giảng viên</h3>
        </div>
        <button onClick={onClose} style={{ background: 'transparent', border: 'none', cursor: 'pointer', color: 'var(--text-secondary)', display: 'flex', padding: 4 }}><X size={20} /></button>
      </div>
      <div style={{ padding: 24, display: 'grid', gap: 18 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
          <div style={{ width: 56, height: 56, borderRadius: '50%', background: 'var(--bg-elevated)', border: '1px solid var(--border)', display: 'flex', alignItems: 'center', justifyContent: 'center', overflow: 'hidden' }}>
            {user.avatar_url ? <img src={user.avatar_url} alt="" style={{ width: '100%', height: '100%', objectFit: 'cover' }} /> : <Users size={24} color="var(--text-muted)" />}
          </div>
          <div style={{ flex: 1 }}>
            <div style={{ fontSize: 17, fontWeight: 700 }}>{user.full_name}</div>
            <div style={{ fontSize: 13, color: 'var(--text-secondary)' }}>{user.email}</div>
          </div>
          <StatusBadge status={user.instructor_status} />
        </div>

        <Field icon={Award} label="Chức danh">{p.headline || <em style={{ color: 'var(--text-muted)' }}>(Chưa có)</em>}</Field>
        <Field icon={ShieldCheck} label="Chuyên môn">{p.expertise || <em style={{ color: 'var(--text-muted)' }}>(Chưa có)</em>}</Field>
        <Field icon={LinkIcon} label="Đường dẫn hồ sơ">{p.profile_url ? <code style={{ background: 'var(--bg-elevated)', padding: '2px 8px', borderRadius: 4, fontSize: 13 }}>{p.profile_url}</code> : <em style={{ color: 'var(--text-muted)' }}>(Chưa có)</em>}</Field>
        <Field icon={FileText} label="Giới thiệu">
          <div style={{ background: 'var(--bg-elevated)', padding: 14, borderRadius: 8, fontSize: 14, lineHeight: 1.6, color: 'var(--text-primary)', whiteSpace: 'pre-wrap' }}>{p.bio || <em style={{ color: 'var(--text-muted)' }}>(Không có thông tin giới thiệu)</em>}</div>
        </Field>
        {p.joined_as_instructor_at && <Field icon={Calendar} label="Đăng ký">{new Date(p.joined_as_instructor_at).toLocaleString('vi-VN')}</Field>}
      </div>
      {isPending && <div style={{ padding: '16px 24px', borderTop: '1px solid var(--border)', display: 'flex', gap: 10, justifyContent: 'flex-end', position: 'sticky', bottom: 0, background: 'var(--bg-surface)' }}>
        <Btn onClick={() => onReject(user.user_id)}>{s.reject}</Btn>
        <Btn variant="primary" onClick={() => onApprove(user.user_id)}>{s.approve}</Btn>
      </div>}
    </div>
  </div>
}

function Field({ icon: Icon, label, children }) {
  return <div>
    <div style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 11, fontWeight: 700, color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: 6 }}>
      <Icon size={12} /> {label}
    </div>
    <div style={{ fontSize: 14 }}>{children}</div>
  </div>
}
function CourseTable({ courses, onModerate }) { return <Table headers={[s.course, s.teacher, s.category, 'Status', s.actions]}>{courses.map(c => <tr key={c.course_id}><td style={cell}>{c.course_name}</td><td style={cell}>{c.instructor_name}</td><td style={cell}>{c.category_name}</td><td style={cell}>{c.status}</td><td style={cell}><Btn variant="primary" onClick={() => onModerate(c.course_id, 'published')}>Publish</Btn> <Btn onClick={() => onModerate(c.course_id, 'draft')}>Draft</Btn> <Btn onClick={() => onModerate(c.course_id, 'archived')}>Archive</Btn></td></tr>)}</Table> }
function CategoryList({ categories, form, setForm, onCreate, onEdit, onSave, onDelete }) {
  const rootCategories = categories.filter(cat => !cat.parent_id)
  return <Section title={s.categories} right={<Btn variant="primary" onClick={onCreate}>{s.createCat}</Btn>}>
    {form && <form onSubmit={e => { e.preventDefault(); onSave(form) }} style={{ padding: 18, display: 'grid', gridTemplateColumns: '1fr 1fr auto auto', gap: 10, borderBottom: '1px solid var(--border)' }}>
      <input className="form-input" value={form.category_name} onChange={e => setForm({ ...form, category_name: e.target.value })} placeholder={s.catName} required />
      <select className="form-input" value={form.parent} onChange={e => setForm({ ...form, parent: e.target.value })}>
        <option value="">{s.rootCat}</option>
        {rootCategories.filter(cat => cat.category_id !== form.category_id).map(cat => <option key={cat.category_id} value={cat.category_id}>{cat.category_name}</option>)}
      </select>
      <Btn variant="primary" type="submit">{s.save}</Btn>
      <Btn onClick={() => setForm(null)}>{s.cancel}</Btn>
    </form>}
    <div style={{ padding: 18, display: 'grid', gap: 10 }}>
      {categories.map(c => <div key={c.category_id} style={{ padding: 12, border: '1px solid var(--border)', borderRadius: 10 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', gap: 12, alignItems: 'center' }}>
          <div><b>{c.category_name}</b>{c.subcategories?.length ? <p style={{ color: 'var(--text-secondary)', marginTop: 4 }}>{c.subcategories.length} {s.childCats}</p> : null}</div>
          <div style={{ display: 'flex', gap: 8 }}><Btn onClick={() => onEdit(c)}>{s.edit}</Btn><Btn onClick={() => onDelete(c.category_id)}>{s.delete}</Btn></div>
        </div>
        {c.subcategories?.length ? <div style={{ marginTop: 10, display: 'grid', gap: 8 }}>{c.subcategories.map(sub => <div key={sub.category_id} style={{ display: 'flex', justifyContent: 'space-between', padding: 10, background: 'var(--bg-elevated)', borderRadius: 8 }}><span>{sub.category_name}</span><span><Btn onClick={() => onEdit(sub)}>{s.edit}</Btn> <Btn onClick={() => onDelete(sub.category_id)}>{s.delete}</Btn></span></div>)}</div> : null}
      </div>)}
    </div>
  </Section>
}
function ReportTable({ reports, onUpdate }) { return <Table headers={[s.reporter, s.target, s.reason, 'Status', s.actions]}>{reports.map(r => <tr key={r.id}><td style={cell}>{r.reporter_name}</td><td style={cell}>{r.target_type} #{r.target_id}</td><td style={cell}>{r.reason}</td><td style={cell}>{r.status}</td><td style={cell}><Btn variant="primary" onClick={() => onUpdate(r.id, 'resolved')}>Resolve</Btn> <Btn onClick={() => onUpdate(r.id, 'dismissed')}>Dismiss</Btn></td></tr>)}</Table> }
function LogList({ logs }) { return <Section title={s.auditLog}><div style={{ padding: 18, display: 'grid', gap: 8 }}>{logs.length ? logs.map(l => <div key={l.id} style={{ padding: 10, borderBottom: '1px solid var(--border)' }}><b>{l.action}</b> - {l.actor_name || 'system'} - {l.target_type} {l.target_id}<div style={{ color: 'var(--text-muted)', fontSize: 12 }}>{new Date(l.created_at).toLocaleString()}</div></div>) : s.noData}</div></Section> }
function SettingsList({ rows, onAdd }) { return <Section title={s.systemSettings} right={<Btn variant="primary" onClick={onAdd}>{s.addSetting}</Btn>}><div style={{ padding: 18, display: 'grid', gap: 10 }}>{rows.length ? rows.map(row => <div key={row.id} style={{ padding: 12, border: '1px solid var(--border)', borderRadius: 10 }}><b>{row.key}</b><pre style={{ whiteSpace: 'pre-wrap', color: 'var(--text-secondary)' }}>{JSON.stringify(row.value, null, 2)}</pre></div>) : s.noData}</div></Section> }
