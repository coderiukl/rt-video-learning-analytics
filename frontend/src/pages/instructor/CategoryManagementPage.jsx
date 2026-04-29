import React, { useEffect, useState } from 'react'
import { categoryApi } from '../../api/client'
import EmptyState from '../../components/common/EmptyState'
import { Tag, PlusCircle, Pencil, Trash2, ChevronRight, X, Check } from 'lucide-react'

export default function CategoryManagementPage() {
  const [categories, setCategories] = useState([])
  const [loading, setLoading] = useState(true)
  const [showForm, setShowForm] = useState(false)
  const [editItem, setEditItem] = useState(null)
  const [form, setForm] = useState({ category_name: '', parent: '' })
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState(null)

  const fetchCategories = () => {
    setLoading(true)
    categoryApi.list()
      .then(res => setCategories(res.data?.results || res.data || []))
      .catch(() => setCategories([]))
      .finally(() => setLoading(false))
  }

  useEffect(fetchCategories, [])

  const rootCats = categories.filter(c => !c.parent_id)
  const getSubCats = (parentId) => categories.filter(c => String(c.parent_id) === String(parentId))

  const openCreate = (parentId = null) => {
    setEditItem(null)
    setForm({ category_name: '', parent: parentId || '' })
    setShowForm(true)
    setError(null)
  }

  const openEdit = (cat) => {
    setEditItem(cat)
    setForm({ category_name: cat.category_name, parent: cat.parent || '' })
    setShowForm(true)
    setError(null)
  }

  const handleSave = async () => {
    setSaving(true); setError(null)
    try {
      const payload = { category_name: form.category_name, parent: form.parent || null }
      if (editItem) {
        await categoryApi.update(editItem.category_id, payload)
      } else {
        await categoryApi.create(payload)
      }
      setShowForm(false)
      fetchCategories()
    } catch (err) {
      setError(err.response?.data?.category_name?.[0] || err.response?.data?.detail || 'Lỗi khi lưu')
    } finally {
      setSaving(false)
    }
  }

  const handleDelete = async (cat) => {
    if (!window.confirm(`Xóa danh mục "${cat.category_name}"?`)) return
    try {
      await categoryApi.delete(cat.category_id)
      fetchCategories()
    } catch (err) {
      alert(err.response?.data?.detail || 'Không thể xóa danh mục này')
    }
  }

  const rowStyle = (isRoot) => ({
    display: 'flex',
    alignItems: 'center',
    padding: '12px 16px',
    borderBottom: '1px solid var(--border-light)',
    background: isRoot ? 'var(--bg-elevated)' : 'transparent',
    gap: 10,
  })

  return (
    <div style={{ maxWidth: 760 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 28 }}>
        <div>
          <h1 style={{ fontSize: 22, fontWeight: 700, marginBottom: 4 }}>Quản lý danh mục</h1>
          <p style={{ color: 'var(--text-secondary)', fontSize: 14 }}>{categories.length} danh mục</p>
        </div>
        <button className="btn btn-primary" onClick={() => openCreate()}>
          <PlusCircle size={16} /> Thêm danh mục
        </button>
      </div>

      {/* Inline form */}
      {showForm && (
        <div className="card" style={{ marginBottom: 20, borderColor: 'var(--accent)' }}>
          <h3 style={{ fontSize: 14, fontWeight: 600, marginBottom: 16 }}>
            {editItem ? `Sửa: ${editItem.category_name}` : 'Tạo danh mục mới'}
          </h3>
          <div style={{ display: 'flex', gap: 12, marginBottom: error ? 12 : 0 }}>
            <input
              value={form.category_name}
              onChange={e => setForm({ ...form, category_name: e.target.value })}
              placeholder="Tên danh mục"
              style={{
                flex: 1, padding: '10px 14px', background: 'var(--bg-elevated)',
                border: '1px solid var(--border)', borderRadius: 'var(--radius-md)',
                color: 'var(--text-primary)', fontSize: 14, outline: 'none',
              }}
            />
            <select
              value={form.parent}
              onChange={e => setForm({ ...form, parent: e.target.value })}
              style={{
                padding: '10px 14px', background: 'var(--bg-elevated)',
                border: '1px solid var(--border)', borderRadius: 'var(--radius-md)',
                color: 'var(--text-primary)', fontSize: 14, outline: 'none',
              }}
            >
              <option value="">Danh mục gốc</option>
              {rootCats.map(c => (
                <option key={c.category_id} value={c.category_id}>{c.category_name}</option>
              ))}
            </select>
            <button className="btn btn-primary btn-sm" onClick={handleSave} disabled={saving || !form.category_name}>
              {saving ? <span className="spinner" style={{ width: 14, height: 14 }} /> : <Check size={16} />}
            </button>
            <button className="btn btn-secondary btn-sm" onClick={() => setShowForm(false)}>
              <X size={16} />
            </button>
          </div>
          {error && <p style={{ color: 'var(--error)', fontSize: 13, marginTop: 8 }}>{error}</p>}
        </div>
      )}

      {loading ? (
        <div style={{ display: 'flex', justifyContent: 'center', padding: 40 }}>
          <div className="spinner" style={{ width: 28, height: 28 }} />
        </div>
      ) : categories.length === 0 ? (
        <EmptyState
          icon={Tag}
          title="Chưa có danh mục nào"
          action={<button className="btn btn-primary" onClick={() => openCreate()}><PlusCircle size={16} />Thêm danh mục</button>}
        />
      ) : (
        <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
          {rootCats.map((cat, idx) => (
            <React.Fragment key={cat.category_id}>
              {/* Root category row */}
              <div style={{
                ...rowStyle(true),
                borderBottom: `1px solid var(--border)`,
                borderTop: idx > 0 ? '2px solid var(--border)' : 'none',
              }}>
                <Tag size={15} color="var(--accent)" />
                <span style={{ fontWeight: 600, fontSize: 14, flex: 1 }}>{cat.category_name}</span>
                <span style={{ fontSize: 12, color: 'var(--text-muted)', marginRight: 8 }}>
                  {getSubCats(cat.category_id).length} danh mục con
                </span>
                <button className="btn btn-secondary btn-sm" onClick={() => openCreate(cat.category_id)} style={{ marginRight: 4 }}>
                  <PlusCircle size={13} />
                </button>
                <button className="btn btn-secondary btn-sm" onClick={() => openEdit(cat)} style={{ marginRight: 4 }}>
                  <Pencil size={13} />
                </button>
                <button className="btn btn-danger btn-sm" onClick={() => handleDelete(cat)}>
                  <Trash2 size={13} />
                </button>
              </div>

              {/* Subcategories */}
              {getSubCats(cat.category_id).map(sub => (
                <div key={sub.category_id} style={{ ...rowStyle(false), paddingLeft: 36 }}>
                  <ChevronRight size={13} color="var(--text-muted)" />
                  <span style={{ fontSize: 14, flex: 1 }}>{sub.category_name}</span>
                  <button className="btn btn-secondary btn-sm" onClick={() => openEdit(sub)} style={{ marginRight: 4 }}>
                    <Pencil size={13} />
                  </button>
                  <button className="btn btn-danger btn-sm" onClick={() => handleDelete(sub)}>
                    <Trash2 size={13} />
                  </button>
                </div>
              ))}
            </React.Fragment>
          ))}
        </div>
      )}
    </div>
  )
}
