import React, { useEffect, useState, useCallback } from 'react'
import { courseApi, categoryApi } from '../../api/client'
import CourseCard from '../../components/common/CourseCard'
import FilterBar from '../../components/forms/FilterBar'
import EmptyState from '../../components/common/EmptyState'
import { CourseCardSkeleton } from '../../components/common/LoadingSkeleton'
import { BookOpen } from 'lucide-react'

export default function CourseDiscoveryPage() {
  const [courses, setCourses] = useState([])
  const [categories, setCategories] = useState([])
  const [loading, setLoading] = useState(true)

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
  }, [fetchCourses])

  return (
    <div>
      <div className="page-header">
        <h1>Khám phá khóa học</h1>
        <p>Tìm kiếm và đăng ký các khóa học phù hợp</p>
      </div>

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
