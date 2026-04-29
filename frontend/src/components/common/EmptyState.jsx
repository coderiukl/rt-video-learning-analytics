import React from 'react'
import { BookOpen } from 'lucide-react'

export default function EmptyState({ icon: Icon = BookOpen, title, description, action }) {
  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      padding: '64px 32px',
      textAlign: 'center',
    }}>
      <div style={{
        width: 64,
        height: 64,
        borderRadius: '50%',
        background: 'var(--bg-elevated)',
        border: '1px solid var(--border)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        marginBottom: 20,
      }}>
        <Icon size={28} color="var(--text-muted)" />
      </div>
      <h3 style={{ fontSize: 16, fontWeight: 600, marginBottom: 8 }}>{title}</h3>
      {description && (
        <p style={{ color: 'var(--text-secondary)', fontSize: 14, maxWidth: 360, marginBottom: 24 }}>
          {description}
        </p>
      )}
      {action}
    </div>
  )
}