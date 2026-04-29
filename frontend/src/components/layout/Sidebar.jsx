import React from 'react'
import { NavLink, useNavigate } from 'react-router-dom'
import { useAuth } from '../../context/AuthContext'
import {
  BookOpen, LayoutDashboard, GraduationCap, User, LogOut,
  PlusCircle, FolderOpen, Settings, Tag, ShieldCheck,
} from 'lucide-react'

function NavItem({ to, icon: Icon, label }) {
  return (
    <NavLink
      to={to}
      style={({ isActive }) => ({
        display: 'flex',
        alignItems: 'center',
        gap: 10,
        padding: '10px 14px',
        borderRadius: 'var(--radius-md)',
        color: isActive ? 'var(--text-primary)' : 'var(--text-secondary)',
        background: isActive ? 'var(--bg-elevated)' : 'transparent',
        fontWeight: isActive ? 600 : 400,
        fontSize: 14,
        textDecoration: 'none',
        transition: 'all 0.15s',
        borderLeft: isActive ? '2px solid var(--accent)' : '2px solid transparent',
      })}
    >
      <Icon size={16} />
      {label}
    </NavLink>
  )
}

export default function Sidebar() {
  const { user, logout, viewMode, setViewMode } = useAuth()
  const navigate = useNavigate()
  const [showTooltip, setShowTooltip] = React.useState(false)

  const handleLogout = async () => {
    await logout()
    navigate('/login')
  }

  const studentLinks = [
    { to: '/student/dashboard', icon: LayoutDashboard, label: 'Dashboard' },
    { to: '/student/my-courses', icon: GraduationCap, label: 'Khóa học của tôi' },
    { to: '/courses', icon: BookOpen, label: 'Khám phá khóa học' },
    { to: '/student/profile', icon: User, label: 'Hồ sơ' },
  ]
 
  const instructorLinks = [
    { to: '/instructor/dashboard', icon: LayoutDashboard, label: 'Dashboard' },
    { to: '/instructor/courses', icon: FolderOpen, label: 'Khóa học của tôi' },
    { to: '/instructor/courses/create', icon: PlusCircle, label: 'Tạo khóa học' },
    { to: '/instructor/categories', icon: Tag, label: 'Danh mục' },
    { to: '/courses', icon: BookOpen, label: 'Khám phá' },
  ]

  const adminLinks = [
    { to: '/admin/dashboard', icon: ShieldCheck, label: 'Quản trị' },
    { to: '/courses', icon: BookOpen, label: 'Khám phá' },
  ]

  const isAdminUser = user?.role === 'admin' || user?.is_staff
  const isInstructorStudentMode = user?.role === 'instructor' && viewMode === 'student'
  const links = isAdminUser ? adminLinks : isInstructorStudentMode ? studentLinks : user?.role === 'instructor' ? instructorLinks : studentLinks

  return (
    <aside style={{
      width: 240,
      flexShrink: 0,
      background: 'var(--bg-surface)',
      borderRight: '1px solid var(--border)',
      display: 'flex',
      flexDirection: 'column',
      height: '100vh',
      position: 'sticky',
      top: 0,
      overflow: 'hidden',
    }}>
      {/* Logo */}
      <div style={{ padding: '24px 20px', borderBottom: '1px solid var(--border)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <div style={{
            width: 34,
            height: 34,
            background: 'var(--accent)',
            borderRadius: 10,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
          }}>
            <BookOpen size={18} color="#fff" />
          </div>
          <div>
            <p style={{ fontWeight: 700, fontSize: 15, lineHeight: 1 }}>LearnFlow</p>
            <p style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 2 }}>Analytics</p>
          </div>
        </div>
      </div>

        {/* Nav */}
        <nav style={{ flex: 1, overflowY: 'auto', padding: '16px 12px', display: 'flex', flexDirection: 'column', gap: 2 }}>
        {links.map((link) => (
            <NavItem key={link.to} {...link} />
        ))}

        {/* Nút chuyển chế độ */}
        <div style={{ marginTop: 12, borderTop: '1px solid var(--border)', paddingTop: 12 }}>
            {isAdminUser ? null : user?.role === 'student' ? (
            // Student → bấm sang Giảng viên
            <button
                onClick={() => navigate('/student/profile')}
                style={{
                display: 'flex', alignItems: 'center', gap: 10,
                padding: '10px 14px', borderRadius: 'var(--radius-md)',
                background: 'transparent', border: 'none', cursor: 'pointer',
                color: 'var(--text-secondary)', fontSize: 14, width: '100%',
                transition: 'all 0.15s',
                }}
                onMouseEnter={e => e.currentTarget.style.background = 'var(--bg-elevated)'}
                onMouseLeave={e => e.currentTarget.style.background = 'transparent'}
            >
                <Settings size={16} />
                Trở thành giảng viên
            </button>
            ) : isInstructorStudentMode ? (
            <button
                onClick={() => {
                    setViewMode('instructor')
                    navigate('/instructor/dashboard')
                }}
                style={{
                    display: 'flex', alignItems: 'center', gap: 10,
                    padding: '10px 14px', borderRadius: 'var(--radius-md)',
                    background: 'transparent', border: 'none', cursor: 'pointer',
                    color: 'var(--text-secondary)', fontSize: 14, width: '100%',
                    transition: 'all 0.15s',
                }}
                onMouseEnter={e => e.currentTarget.style.background = 'var(--bg-elevated)'}
                onMouseLeave={e => e.currentTarget.style.background = 'transparent'}
            >
                <Settings size={16} />
                Giảng viên
            </button>
            ) : (
            // Instructor → hover tooltip sang Học viên
            <div style={{ position: 'relative' }}>
                <button
                onClick={() => {
                    setViewMode('student')
                    navigate('/student/dashboard')
                }}
                onMouseEnter={() => setShowTooltip(true)}
                onMouseLeave={() => setShowTooltip(false)}
                style={{
                    display: 'flex', alignItems: 'center', gap: 10,
                    padding: '10px 14px', borderRadius: 'var(--radius-md)',
                    background: 'transparent', border: 'none', cursor: 'pointer',
                    color: 'var(--text-secondary)', fontSize: 14, width: '100%',
                    transition: 'all 0.15s',
                }}
                >
                <User size={16} />
                Học viên
                </button>

                {showTooltip && (
                <div style={{
                    position: 'absolute', left: '100%', top: '50%',
                    transform: 'translateY(-50%)', marginLeft: 10,
                    background: 'var(--bg-elevated)', border: '1px solid var(--border)',
                    borderRadius: 'var(--radius-md)', padding: '10px 14px',
                    fontSize: 12, color: 'var(--text-secondary)',
                    width: 220, lineHeight: 1.5, zIndex: 100,
                    boxShadow: '0 4px 12px rgba(0,0,0,0.3)',
                }}>
                    Chuyển sang chế độ xem của học viên tại đây — quay lại các khóa học bạn đang tham gia.
                </div>
                )}
            </div>
            )}
        </div>
        </nav>

      {/* User section */}
      <div style={{ padding: 16, borderTop: '1px solid var(--border)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 12 }}>
          <div style={{
            width: 34,
            height: 34,
            borderRadius: '50%',
            background: 'var(--accent-dim)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontSize: 14,
            fontWeight: 700,
            color: 'var(--accent)',
            flexShrink: 0,
          }}>
            {user?.full_name?.[0]?.toUpperCase() || 'U'}
          </div>
          <div style={{ overflow: 'hidden' }}>
            <p style={{ fontSize: 13, fontWeight: 600, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
              {user?.full_name}
            </p>
            <p style={{ fontSize: 11, color: 'var(--text-muted)', textTransform: 'capitalize' }}>{user?.role}</p>
          </div>
        </div>
        <button
          className="btn btn-secondary btn-sm"
          style={{ width: '100%', justifyContent: 'center' }}
          onClick={handleLogout}
        >
          <LogOut size={14} />
          Đăng xuất
        </button>
      </div>
    </aside>
  )
}
