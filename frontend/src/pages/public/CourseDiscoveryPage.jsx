import React, { useEffect, useState, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { courseApi, categoryApi, analyticsApi } from '../../api/client'
import { useAuth } from '../../context/AuthContext'
import CourseCard from '../../components/common/CourseCard'
import FilterBar from '../../components/forms/FilterBar'
import EmptyState from '../../components/common/EmptyState'
import { CourseCardSkeleton } from '../../components/common/LoadingSkeleton'
import { BookOpen, Sparkles, User } from 'lucide-react'

export default function CourseDiscoveryPage() {
  const { user } = useAuth()
  const navigate = useNavigate()
  const [courses, setCourses] = useState([])
  const [categories, setCategories] = useState([])
  const [loading, setLoading] = useState(true)
  
  const [recommendations, setRecommendations] = useState([])
  const [recommendationsLoading, setRecommendationsLoading] = useState(false)

  const fetchCategories = async () => {
    try {
      const res = await categoryApi.list()
      setCategories(res.data?.results || res.data || [])
    } catch (_) {}
  }

  const fetchCourses = useCallback(async (filters = {}) => {
    setLoading(true)
    try {
      const params = {}
      if (filters.search) params.search = filters.search
      if (filters.category) params.category = filters.category
      if (filters.level) params.level = filters.level
      if (filters.language) params.language = filters.language
      const res = await courseApi.list(params)
      setCourses(res.data?.results || res.data || [])
    } catch (_) {
      setCourses([])
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchCategories()
    fetchCourses()
    
    if (user && user.role === 'student') {
      setRecommendationsLoading(true)
      analyticsApi.personalizedCourseRecommendations()
        .then(res => setRecommendations(res.data?.recommendations || []))
        .catch(() => setRecommendations([]))
        .finally(() => setRecommendationsLoading(false))
    }
  }, [fetchCourses, user])

  return (
    <div>
      <div className="page-header">
        <h1>Khám phá khóa học</h1>
        <p>Tìm kiếm và đăng ký các khóa học phù hợp</p>
      </div>

      {user && user.role === 'student' && (recommendationsLoading || recommendations.length > 0) && (
        <div style={{ marginBottom: 40 }}>
          <h2 style={{ fontSize: 18, fontWeight: 700, marginBottom: 16, display: 'flex', alignItems: 'center', gap: 8, color: 'var(--accent)' }}>
            <Sparkles size={20} /> Đề xuất riêng cho bạn
          </h2>
          {recommendationsLoading ? (
            <div className="grid-3">
              {Array.from({ length: 3 }).map((_, i) => <CourseCardSkeleton key={i} />)}
            </div>
          ) : (
            <div className="grid-3">
              {recommendations.slice(0, 4).map((rec) => (
                <div 
                  key={rec.course_id}
                  onClick={() => navigate(`/courses/${rec.course_id}`)}
                  style={{
                    padding: 16,
                    borderRadius: 'var(--radius-md)',
                    background: 'var(--bg-elevated)',
                    border: '1px solid var(--border)',
                    cursor: 'pointer',
                    transition: 'all 0.2s ease',
                  }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.borderColor = 'var(--accent)'
                    e.currentTarget.style.transform = 'translateY(-4px)'
                    e.currentTarget.style.boxShadow = '0 8px 24px rgba(0,0,0,0.12)'
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.borderColor = 'var(--border)'
                    e.currentTarget.style.transform = 'none'
                    e.currentTarget.style.boxShadow = 'none'
                  }}
                >
                  <h3 style={{ fontSize: 16, fontWeight: 700, marginBottom: 8, lineHeight: 1.4, display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical', overflow: 'hidden' }}>
                    {rec.course_name}
                  </h3>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 13, color: 'var(--text-muted)' }}>
                    <User size={13} />
                    <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                      {rec.instructor_name}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      <FilterBar onFilter={fetchCourses} categories={categories} />

      {loading ? (
        <div className="grid-3">
          {Array.from({ length: 6 }).map((_, i) => <CourseCardSkeleton key={i} />)}
        </div>
      ) : courses.length === 0 ? (
        <EmptyState
          icon={BookOpen}
          title="Không tìm thấy khóa học"
          description="Thử thay đổi bộ lọc hoặc từ khóa tìm kiếm"
        />
      ) : (
        <div className="grid-3">
          {courses.map((course) => (
            <CourseCard key={course.course_id} course={course} />
          ))}
        </div>
      )}
    </div>
  )
}
