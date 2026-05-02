import React from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import ProtectedRoute from './components/common/ProtectedRoute'
import AppLayout from './components/layout/AppLayout'

// Auth pages
import LoginPage from './pages/auth/LoginPage'
import RegisterPage from './pages/auth/RegisterPage'
import ForgotPasswordPage from './pages/auth/ForgotPasswordPage'

// Public pages
import CourseDiscoveryPage from './pages/public/CourseDiscoveryPage'
import CourseDetailPage from './pages/public/CourseDetailPage'

// Student pages
import StudentDashboard from './pages/student/StudentDashboard'
import MyCoursesPage from './pages/student/MyCoursesPage'
import ProfilePage from './pages/student/ProfilePage'
import CourseLearnPage from './pages/student/CourseLearnPage'

// Instructor pages
import InstructorDashboard from './pages/instructor/InstructorDashboard'
import InstructorCoursesPage from './pages/instructor/InstructorCoursesPage'
import CreateCoursePage from './pages/instructor/CreateCoursePage'
import EditCoursePage from './pages/instructor/EditCoursePage'
import CourseVideosPage from './pages/instructor/CourseVideosPage'
import CategoryManagementPage from './pages/instructor/CategoryManagementPage'
import CourseAnalyticsPage from './pages/instructor/CourseAnalyticsPage'
import AdminDashboardPage from './pages/admin/AdminDashboardPage'

// Layout wrapper for authenticated pages
function AuthLayout({ children }) {
  return (
    <AppLayout>
      {children}
    </AppLayout>
  )
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
          {/* Public auth routes */}
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />
          <Route path="/forgot-password" element={<ForgotPasswordPage />} />

          {/* Public course routes (accessible without login, but with layout if logged in) */}
          <Route path="/courses" element={<AuthLayout><CourseDiscoveryPage /></AuthLayout>} />
          <Route path="/courses/:id" element={<AuthLayout><CourseDetailPage /></AuthLayout>} />

          {/* Student routes */}
          <Route path="/student/dashboard" element={
            <ProtectedRoute role="student">
              <AuthLayout><StudentDashboard /></AuthLayout>
            </ProtectedRoute>
          } />
          <Route path="/student/my-courses" element={
            <ProtectedRoute role="student">
              <AuthLayout><MyCoursesPage /></AuthLayout>
            </ProtectedRoute>
          } />
          <Route path="/student/profile" element={
            <ProtectedRoute role="student">
              <AuthLayout><ProfilePage /></AuthLayout>
            </ProtectedRoute>
          } />
          <Route path="/courses/:id/learn" element={
            <ProtectedRoute role="student">
              <AuthLayout><CourseLearnPage /></AuthLayout>
            </ProtectedRoute>
          } />

          {/* Instructor routes */}
          <Route path="/instructor/dashboard" element={
            <ProtectedRoute role="instructor">
              <AuthLayout><InstructorDashboard /></AuthLayout>
            </ProtectedRoute>
          } />
          <Route path="/instructor/courses" element={
            <ProtectedRoute role="instructor">
              <AuthLayout><InstructorCoursesPage /></AuthLayout>
            </ProtectedRoute>
          } />
          <Route path="/instructor/courses/create" element={
            <ProtectedRoute role="instructor">
              <AuthLayout><CreateCoursePage /></AuthLayout>
            </ProtectedRoute>
          } />
          <Route path="/instructor/courses/:id/edit" element={
            <ProtectedRoute role="instructor">
              <AuthLayout><EditCoursePage /></AuthLayout>
            </ProtectedRoute>
          } />
          <Route path="/instructor/courses/:id/videos" element={
            <ProtectedRoute role="instructor">
              <AuthLayout><CourseVideosPage /></AuthLayout>
            </ProtectedRoute>
          } />
          <Route path="/instructor/courses/:id/analytics" element={
            <ProtectedRoute role="instructor">
              <AuthLayout><CourseAnalyticsPage /></AuthLayout>
            </ProtectedRoute>
          } />
          <Route path="/instructor/categories" element={
            <ProtectedRoute role="instructor">
              <AuthLayout><CategoryManagementPage /></AuthLayout>
            </ProtectedRoute>
          } />

          {/* Admin routes */}
          <Route path="/admin/dashboard" element={
            <ProtectedRoute role="admin">
              <AuthLayout><AdminDashboardPage /></AuthLayout>
            </ProtectedRoute>
          } />

          {/* Default redirects */}
          <Route path="/" element={<Navigate to="/courses" replace />} />
          <Route path="*" element={<Navigate to="/courses" replace />} />
      </Routes>
    </BrowserRouter>
  )
}
