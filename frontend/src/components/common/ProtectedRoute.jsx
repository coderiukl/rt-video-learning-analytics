import React from 'react'
import { Navigate, useLocation } from 'react-router-dom'
import { useAuth } from '../../context/AuthContext'

export default function ProtectedRoute({ children, role }) {
  const { user, loading } = useAuth()
  const location = useLocation()

  if (loading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }}>
        <div className="spinner" style={{ width: 32, height: 32 }} />
      </div>
    )
  }

  if (!user) {
    return <Navigate to="/login" state={{ from: location }} replace />
  }

  const isAdminUser = user.role === 'admin' || user.is_staff
  const canUseStudentMode = role === 'student' && user.role === 'instructor'
  const canUseAdminRoute = role === 'admin' && isAdminUser

  if (role && user.role !== role && !canUseStudentMode && !canUseAdminRoute) {
    // Redirect về dashboard phù hợp với role
    if (user.role === 'student') return <Navigate to="/student/dashboard" replace />
    if (user.role === 'instructor') return <Navigate to="/instructor/dashboard" replace />
    if (isAdminUser) return <Navigate to="/admin/dashboard" replace />
    return <Navigate to="/courses" replace />
  }

  return children
}
