import React, { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { courseApi } from '../../api/client'
import CourseCard from '../../components/common/CourseCard'
import EmptyState from '../../components/common/EmptyState'
import { CourseCardSkeleton } from '../../components/common/LoadingSkeleton'
import { BookOpen, PlusCircle } from 'lucide-react'

export default function InstructorCoursesPage() {
  const [courses, setCourses] = useState([])
  const [loading, setLoading] = useState(true)
  const [deleting, setDeleting] = useState(null)
  const navigate = useNavigate()

  const fetchCourses = () => {
    setLoading(true)
    courseApi.instructorCourses()
      .then(res => setCourses(res.data?.results || res.data || []))
      .catch(() => setCourses([]))
      .finally(() => setLoading(false))
  }

  useEffect(fetchCourses, [])

  const handleDelete = async (course) => {
    if (!window.confirm(`Xóa khóa học "${course.course_name}"?`)) return
    setDeleting(course.course_id)
    try {
      await courseApi.delete(course.course_id)
      fetchCourses()
    } catch (err) {
      alert(err.response?.data?.detail || 'Không thể xóa khóa học')
    } finally {
      setDeleting(null)
    }
  }

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 28 }}>
        <div>
          <h1 style={{ fontSize: 22, fontWeight: 700, marginBottom: 4 }}>Khóa học của tôi</h1>
          <p style={{ color: 'var(--text-secondary)', fontSize: 14 }}>{courses.length} khóa học</p>
        </div>
        <button
          className="btn btn-primary"
          onClick={() => navigate('/instructor/courses/create')}
        >
          <PlusCircle size={16} /> Tạo mới
        </button>
      </div>

      {loading ? (
        <div className="grid-3">
          {Array.from({ length: 4 }).map((_, i) => <CourseCardSkeleton key={i} />)}
        </div>
      ) : courses.length === 0 ? (
        <EmptyState
          icon={BookOpen}
          title="Chưa có khóa học nào"
          description="Tạo khóa học đầu tiên của bạn để bắt đầu giảng dạy"
          action={
            <button className="btn btn-primary" onClick={() => navigate('/instructor/courses/create')}>
              <PlusCircle size={16} /> Tạo khóa học
            </button>
          }
        />
      ) : (
        <div className="grid-3">
          {courses.map(course => (
            <CourseCard
              key={course.course_id}
              course={course}
              showActions
              onEdit={(c) => navigate(`/instructor/courses/${c.course_id}/edit`)}
              onVideos={(c) => navigate(`/instructor/courses/${c.course_id}/videos`)}
              onDelete={handleDelete}
            />
          ))}
        </div>
      )}
    </div>
  )
}
