import React, { useState } from 'react'
import { Search, X } from 'lucide-react'

export default function FilterBar({ onFilter, categories = [] }) {
  const [filters, setFilters] = useState({ search: '', category: '', level: '', language: '' })

  const handleChange = (e) => {
    const updated = { ...filters, [e.target.name]: e.target.value }
    setFilters(updated)
    onFilter(updated)
  }

  const clearAll = () => {
    const cleared = { search: '', category: '', level: '', language: '' }
    setFilters(cleared)
    onFilter(cleared)
  }

  const hasFilter = Object.values(filters).some(Boolean)

  const selectStyle = {
    padding: '9px 14px',
    background: 'var(--bg-elevated)',
    border: '1px solid var(--border)',
    borderRadius: 'var(--radius-md)',
    color: filters.category || filters.level || filters.language ? 'var(--text-primary)' : 'var(--text-secondary)',
    fontSize: 13,
    outline: 'none',
    cursor: 'pointer',
  }

  return (
    <div style={{
      display: 'flex',
      gap: 12,
      flexWrap: 'wrap',
      alignItems: 'center',
      padding: '16px 20px',
      background: 'var(--bg-surface)',
      border: '1px solid var(--border)',
      borderRadius: 'var(--radius-lg)',
      marginBottom: 24,
    }}>
      {/* Search */}
      <div style={{ position: 'relative', flex: '1 1 240px', minWidth: 200 }}>
        <Search size={16} style={{ position: 'absolute', left: 12, top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }} />
        <input
          name="search"
          value={filters.search}
          onChange={handleChange}
          placeholder="Tìm kiếm khóa học..."
          style={{
            width: '100%',
            padding: '9px 14px 9px 36px',
            background: 'var(--bg-elevated)',
            border: '1px solid var(--border)',
            borderRadius: 'var(--radius-md)',
            color: 'var(--text-primary)',
            fontSize: 13,
            outline: 'none',
          }}
        />
      </div>

      {/* Category */}
      <select name="category" value={filters.category} onChange={handleChange} style={selectStyle}>
        <option value="">Tất cả danh mục</option>
        {categories.map((cat) => (
          <option key={cat.category_id} value={cat.category_id}>{cat.category_name}</option>
        ))}
      </select>

      {/* Level */}
      <select name="level" value={filters.level} onChange={handleChange} style={selectStyle}>
        <option value="">Tất cả cấp độ</option>
        <option value="beginner">Cơ bản</option>
        <option value="intermediate">Trung cấp</option>
        <option value="advanced">Nâng cao</option>
      </select>

      {/* Language */}
      <select name="language" value={filters.language} onChange={handleChange} style={selectStyle}>
        <option value="">Tất cả ngôn ngữ</option>
        <option value="vi">Tiếng Việt</option>
        <option value="en">English</option>
      </select>

      {/* Clear */}
      {hasFilter && (
        <button className="btn btn-secondary btn-sm" onClick={clearAll} style={{ gap: 6 }}>
          <X size={14} /> Xóa lọc
        </button>
      )}
    </div>
  )
}
