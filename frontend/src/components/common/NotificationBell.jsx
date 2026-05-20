import React, { useEffect, useState } from 'react'
import { Bell } from 'lucide-react'
import { notificationApi } from '../../api/client'

export default function NotificationBell() {
  const [items, setItems] = useState([])
  const [open, setOpen] = useState(false)

  const load = () => notificationApi.list().then(res => setItems(res.data || [])).catch(() => setItems([]))
  useEffect(() => { load() }, [])

  const unread = items.filter(i => !i.is_read).length
  const markAll = async () => { await notificationApi.readAll(); load() }

  return <div style={{ position: 'relative' }}>
    <button className="btn btn-secondary btn-sm" onClick={() => setOpen(!open)} style={{ position: 'relative' }}>
      <Bell size={16} />
      Thông báo
      {unread > 0 && <span style={{ marginLeft: 6, background: '#ef4444', color: '#fff', borderRadius: 999, padding: '1px 7px', fontSize: 11 }}>{unread}</span>}
    </button>
    {open && <div style={{ position: 'absolute', right: 0, top: 42, width: 360, maxHeight: 420, overflowY: 'auto', background: 'var(--bg-surface)', border: '1px solid var(--border)', borderRadius: 14, boxShadow: '0 12px 30px rgba(0,0,0,.25)', zIndex: 50 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: 14, borderBottom: '1px solid var(--border)' }}>
        <b>Thông báo</b>
        <button className="btn btn-secondary btn-sm" onClick={markAll}>Đọc hết</button>
      </div>
      {items.length === 0 ? <p style={{ padding: 16, color: 'var(--text-muted)' }}>Chưa có thông báo.</p> : items.map(item => <div key={item.id} style={{ padding: 14, borderBottom: '1px solid var(--border)', background: item.is_read ? 'transparent' : 'var(--bg-elevated)' }}>
        <div style={{ fontWeight: 700, marginBottom: 4 }}>{item.title}</div>
        <div style={{ color: 'var(--text-secondary)', fontSize: 13, lineHeight: 1.5 }}>{item.message}</div>
        <div style={{ color: 'var(--text-muted)', fontSize: 11, marginTop: 6 }}>{new Date(item.created_at).toLocaleString()}</div>
      </div>)}
    </div>}
  </div>
}
