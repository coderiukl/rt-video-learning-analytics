import React from 'react'

function SkeletonBox({ width = '100%', height = 16, borderRadius = 6, style = {} }) {
  return (
    <div style={{
      width,
      height,
      borderRadius,
      background: 'linear-gradient(90deg, var(--bg-elevated) 25%, var(--bg-hover) 50%, var(--bg-elevated) 75%)',
      backgroundSize: '200% 100%',
      animation: 'shimmer 1.5s infinite',
      ...style,
    }} />
  )
}

export function CourseCardSkeleton() {
  return (
    <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
      <SkeletonBox height={160} borderRadius="16px 16px 0 0" />
      <div style={{ padding: 20, display: 'flex', flexDirection: 'column', gap: 12 }}>
        <SkeletonBox height={14} width="60%" />
        <SkeletonBox height={18} />
        <SkeletonBox height={14} width="80%" />
        <div style={{ display: 'flex', gap: 8 }}>
          <SkeletonBox height={24} width={70} borderRadius={999} />
          <SkeletonBox height={24} width={70} borderRadius={999} />
        </div>
      </div>
    </div>
  )
}

export function StatCardSkeleton() {
  return (
    <div className="card">
      <SkeletonBox height={14} width="50%" style={{ marginBottom: 16 }} />
      <SkeletonBox height={32} width="40%" />
    </div>
  )
}

export function TableRowSkeleton({ cols = 4 }) {
  return (
    <tr>
      {Array.from({ length: cols }).map((_, i) => (
        <td key={i} style={{ padding: '16px 20px' }}>
          <SkeletonBox height={14} width={i === 0 ? '80%' : '60%'} />
        </td>
      ))}
    </tr>
  )
}

// CSS animation cho shimmer - thêm vào index.css
// @keyframes shimmer { to { background-position: -200% 0; } }
// Nếu chưa có, thêm dòng sau vào src/index.css:
// @keyframes shimmer { 0% { background-position: 200% 0; } 100% { background-position: -200% 0; } }

export default { CourseCardSkeleton, StatCardSkeleton, TableRowSkeleton }