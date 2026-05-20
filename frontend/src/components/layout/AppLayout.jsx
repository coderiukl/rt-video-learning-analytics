import React from 'react'
import Sidebar from './Sidebar'
import NotificationBell from '../common/NotificationBell'

export default function AppLayout({ children }) {
  return (
    <div style={{ display: 'flex', minHeight: '100vh' }}>
      <Sidebar />
      <main style={{
        flex: 1,
        overflowY: 'auto',
        padding: '24px 36px 32px',
        minWidth: 0,
      }}>
        <div style={{ display: 'flex', justifyContent: 'flex-end', marginBottom: 18 }}>
          <NotificationBell />
        </div>
        {children}
      </main>
    </div>
  )
}
