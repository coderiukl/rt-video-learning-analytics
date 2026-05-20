import React, { useEffect, useState } from 'react'
import { studentExtrasApi } from '../../api/client'

const card = { background: 'var(--bg-surface)', border: '1px solid var(--border)', borderRadius: 16, padding: 20, marginBottom: 20 }

export default function StudentLearningHubPage() {
  const [wishlist, setWishlist] = useState([])
  const [certs, setCerts] = useState([])
  const [goals, setGoals] = useState([])
  const [watching, setWatching] = useState([])
  const [notes, setNotes] = useState([])
  const [title, setTitle] = useState('')
  const [q, setQ] = useState('')

  const load = async () => {
    const [w, c, g, cw, n] = await Promise.all([
      studentExtrasApi.wishlist(), studentExtrasApi.certificates(), studentExtrasApi.goals(), studentExtrasApi.continueWatching(), studentExtrasApi.searchNotes(q),
    ])
    setWishlist(w.data || [])
    setCerts(c.data || [])
    setGoals(g.data || [])
    setWatching(cw.data || [])
    setNotes(n.data || [])
  }
  useEffect(() => { load() }, [])

  const addGoal = async (e) => {
    e.preventDefault()
    if (!title.trim()) return
    await studentExtrasApi.createGoal({ title })
    setTitle('')
    load()
  }
  const toggleGoal = async (g) => { await studentExtrasApi.updateGoal(g.id, { is_completed: !g.is_completed }); load() }
  const deleteGoal = async (id) => { await studentExtrasApi.deleteGoal(id); load() }
  const removeWishlist = async (courseId) => { await studentExtrasApi.removeWishlist(courseId); load() }
  const issueCertificate = async (courseId) => { await studentExtrasApi.issueCertificate(courseId); load() }

  return <div>
    <h1 style={{ marginBottom: 20 }}>Learning Hub</h1>

    <section style={card}><h2>Tiếp tục học</h2>
      {watching.map(v => <div key={v.video_id} style={{ padding: 10, borderBottom: '1px solid var(--border)' }}>{v.course_name} — {v.title} ({v.watched_seconds}/{v.duration_seconds}s)</div>)}
      {!watching.length && <p style={{ color: 'var(--text-muted)' }}>Chưa có video đang học dở.</p>}
    </section>

    <section style={card}><h2>Mục tiêu học tập</h2>
      <form onSubmit={addGoal} style={{ display: 'flex', gap: 8, margin: '12px 0' }}><input className="form-input" value={title} onChange={e => setTitle(e.target.value)} placeholder="VD: Hoàn thành React trong tháng này" /><button className="btn btn-primary">Thêm</button></form>
      {goals.map(g => <div key={g.id} style={{ display: 'flex', alignItems: 'center', gap: 8, padding: 8 }}><label style={{ flex: 1 }}><input type="checkbox" checked={g.is_completed} onChange={() => toggleGoal(g)} /> {g.title}</label><button className="btn btn-danger btn-sm" onClick={() => deleteGoal(g.id)}>Xóa</button></div>)}
    </section>

    <section style={card}><h2>Wishlist</h2>
      {wishlist.map(i => <div key={i.id} style={{ display: 'flex', justifyContent: 'space-between', gap: 12, padding: 10, borderBottom: '1px solid var(--border)' }}><div><b>{i.course?.course_name}</b><p style={{ color: 'var(--text-muted)' }}>{i.course?.instructor_name}</p></div><button className="btn btn-secondary btn-sm" onClick={() => removeWishlist(i.course?.course_id)}>Bỏ lưu</button></div>)}
      {!wishlist.length && <p style={{ color: 'var(--text-muted)' }}>Wishlist trống.</p>}
    </section>

    <section style={card}><h2>Chứng chỉ</h2>
      {certs.map(c => <div key={c.id} style={{ padding: 10, borderBottom: '1px solid var(--border)' }}>{c.course_name} — <code>{c.certificate_code}</code></div>)}
      {!certs.length && <p style={{ color: 'var(--text-muted)' }}>Chưa có chứng chỉ.</p>}
      <div style={{ display: 'flex', gap: 8, marginTop: 12 }}><input className="form-input" placeholder="Course ID để cấp chứng chỉ" onKeyDown={e => { if (e.key === 'Enter' && e.currentTarget.value) issueCertificate(e.currentTarget.value) }} /><button className="btn btn-secondary" onClick={e => issueCertificate(e.currentTarget.previousSibling.value)}>Cấp</button></div>
    </section>

    <section style={card}><h2>Tìm ghi chú</h2>
      <div style={{ display: 'flex', gap: 8, margin: '12px 0' }}><input className="form-input" value={q} onChange={e => setQ(e.target.value)} placeholder="Từ khóa" /><button className="btn btn-secondary" onClick={load}>Tìm</button></div>
      {notes.map(n => <div key={n.note_id} style={{ padding: 10, borderBottom: '1px solid var(--border)' }}>{n.timestamp_seconds}s — {n.content}</div>)}
    </section>
  </div>
}
