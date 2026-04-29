import React from 'react'

export default function StatCard({ title, value, subtitle, icon: Icon, color = 'var(--accent)', badge }) {
  return (
    <div className="card" style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
      <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between' }}>
        <div>
          <p style={{ fontSize: 12, color: 'var(--text-secondary)', fontWeight: 500, marginBottom: 8, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
            {title}
          </p>
          <p style={{ fontSize: 32, fontWeight: 700, color: 'var(--text-primary)', lineHeight: 1 }}>
            {value ?? '—'}
          </p>
          {subtitle && (
            <p style={{ fontSize: 12, color: 'var(--text-secondary)', marginTop: 6 }}>{subtitle}</p>
          )}
        </div>
        {Icon && (
          <div style={{
            width: 44,
            height: 44,
            borderRadius: `var(--radius-md)`,
            background: 'var(--bg-elevated)',
            border: '1px solid var(--border)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            flexShrink: 0,
          }}>
            <Icon size={20} color={color} />
          </div>
        )}
      </div>
      {badge}
    </div>
  )
}