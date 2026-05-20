import axios from 'axios'

const BASE_URL = 'http://127.0.0.1:8000'

const apiClient = axios.create({
    baseURL: BASE_URL,
    headers: {
        'Content-Type': 'application/json',
    },
})

// Request interceptor: gắn token vào header
apiClient.interceptors.request.use(
    (config) => {
        const token = localStorage.getItem('access_token')
        if (token) {
            config.headers.Authorization = `Bearer ${token}`
        }
        return config
    },
    (error) => Promise.reject(error)
)

// Response interceptor: tự động refresh token khi 401
apiClient.interceptors.response.use(
    (response) => response,
    async (error) => {
        const originalRequest = error.config
        
        if (error.response?.status === 401 && !originalRequest._retry) {
            originalRequest._retry = true
            const refreshToken = localStorage.getItem('refresh_token')

            if (refreshToken) {
                try {
                    const res = await axios.post(`${BASE_URL}/api/auth/refresh/`, {
                        refresh: refreshToken,
                    })
                    const newAccess = res.data.access
                    localStorage.setItem('access_token', newAccess)
                    originalRequest.headers.Authorization = `Bearer ${newAccess}`
                    return apiClient(originalRequest)
                } catch (refreshError) {
                    localStorage.removeItem('access_token')
                    localStorage.removeItem('refresh_token')
                    window.location.href = '/login'
                    return Promise.reject(refreshError)
                }
            } else {
                window.location.href = '/login'
            }
        }
        return Promise.reject(error)
    }
)

// Auth
export const authApi = {
    register: (data) => apiClient.post('/api/auth/register/', data),
    login: (data) => apiClient.post('/api/auth/login/', data),
    logout: (data) => apiClient.post('/api/auth/logout/', data),
    me: () => apiClient.get('/api/auth/me/'),
    updateProfile: (data) => apiClient.patch('/api/auth/me/', data),
    changePassword: (data) => apiClient.post('/api/auth/change-password/', data),
    getInstructorProfile: () => apiClient.get('/api/auth/instructor-profile/'),
    applyInstructorProfile: (data) => apiClient.post('/api/auth/instructor-profile/', data),
    sendOtp: (data) => apiClient.post('/api/auth/forgot-password/send-otp/', data),
    verifyOtp: (data) => apiClient.post('/api/auth/forgot-password/verify-otp/', data),
    resetPassword: (data) => apiClient.post('/api/auth/forgot-password/reset/', data),
}

// Categories
export const categoryApi = {
    list: () => apiClient.get('/api/courses/categories/'),
    create: (data) => apiClient.post('/api/courses/categories/', data),
    get: (id) => apiClient.get(`/api/courses/categories/${id}/`),
    update: (id, data) => apiClient.put(`/api/courses/categories/${id}/`, data),
    delete: (id) => apiClient.delete(`/api/courses/categories/${id}/`),
}

// Courses
export const courseApi = {
    list: (params) => apiClient.get('/api/courses/', { params }),
    get: (id) => apiClient.get(`/api/courses/${id}/`),
    getManage: (id) => apiClient.get(`/api/courses/${id}/manage/`),
    create: (data) => apiClient.post('/api/courses/create/', data),
    update: (id, data) => apiClient.put(`/api/courses/${id}/manage/`, data),
    delete: (id) => apiClient.delete(`/api/courses/${id}/manage/`),
    enroll: (id) => apiClient.post(`/api/courses/${id}/enroll/`),
    myCourses: () => apiClient.get('/api/courses/my-course/'),
    instructorCourses: () => apiClient.get('/api/courses/instructor-course/'),
}

export const adminApi = {
    dashboard: (params) => apiClient.get('/api/admin/dashboard/', { params }),
    approveInstructor: (userId) => apiClient.post(`/api/admin/instructors/${userId}/approve/`),
}

export const videoApi = {
    list: (courseId) => apiClient.get(`/api/videos/courses/${courseId}/`),
    create: (courseId, data) => apiClient.post(`/api/videos/courses/${courseId}/`, data, {
        headers: { 'Content-Type': 'multipart/form-data' },
    }),
    update: (videoId, data) => apiClient.put(`/api/videos/${videoId}/`, data, {
        headers: { 'Content-Type': 'multipart/form-data' },
    }),
    delete: (videoId) => apiClient.delete(`/api/videos/${videoId}/`),
}

export const progressApi = {
    get: (videoId) => apiClient.get(`/api/videos/${videoId}/progress/`),
    update: (videoId, data) => apiClient.post(`/api/videos/${videoId}/progress/`, data),
}

export const noteApi = {
    list: (videoId) => apiClient.get(`/api/videos/${videoId}/notes/`),
    create: (videoId, data) => apiClient.post(`/api/videos/${videoId}/notes/`, data),
    update: (noteId, data) => apiClient.put(`/api/videos/notes/${noteId}/`, data),
    delete: (noteId) => apiClient.delete(`/api/videos/notes/${noteId}/`),
}

export const analyticsApi = {
    trackEvent: (data) => apiClient.post('/api/analytics/events/', data),
    instructorBehavior: () => apiClient.get('/api/analytics/instructor/behavior/'),
    courseBehavior: (courseId) => apiClient.get(`/api/analytics/courses/${courseId}/behavior/`),
    courseAtRisk: (courseId) => apiClient.get(`/api/analytics/courses/${courseId}/at-risk/`),
    videoHeatmap: (videoId) => apiClient.get(`/api/analytics/videos/${videoId}/heatmap/`),
    adminBehavior: (params) => apiClient.get('/api/analytics/admin/behavior/', { params }),
    // Dropout Prediction Model
    trainDropoutModel: () => apiClient.post('/api/analytics/dropout-model/train/'),
    dropoutModelStatus: () => apiClient.get('/api/analytics/dropout-model/status/'),
    // Learning Styles
    learningStyles: (courseId) => apiClient.get(`/api/analytics/courses/${courseId}/learning-styles/`),
    // Course Recommendations
    courseRecommendations: (courseId) => apiClient.get(`/api/analytics/courses/${courseId}/recommendations/`),
    // Personalized Recommendations
    personalizedCourseRecommendations: () => apiClient.get(`/api/analytics/courses/personalized-recommendations/`),
}

export default apiClient

export const notificationApi = {
    list: (params) => apiClient.get('/api/notifications/', { params }),
    readAll: () => apiClient.post('/api/notifications/read/'),
    read: (id) => apiClient.post(`/api/notifications/${id}/read/`),
}

export const adminManageApi = {
    users: (params) => apiClient.get('/api/admin/users/', { params }),
    updateUser: (userId, data) => apiClient.patch(`/api/admin/users/${userId}/`, data),
    lockUser: (userId) => apiClient.delete(`/api/admin/users/${userId}/`),
    resetPassword: (userId, data) => apiClient.post(`/api/admin/users/${userId}/reset-password/`, data),
    rejectInstructor: (userId, data) => apiClient.post(`/api/admin/instructors/${userId}/reject/`, data),
    courses: (params) => apiClient.get('/api/admin/courses/', { params }),
    moderateCourse: (courseId, data) => apiClient.patch(`/api/admin/courses/${courseId}/moderate/`, data),
    auditLogs: () => apiClient.get('/api/admin/audit-logs/'),
    settings: () => apiClient.get('/api/admin/settings/'),
    saveSetting: (data) => apiClient.post('/api/admin/settings/', data),
}

export const studentExtrasApi = {
    wishlist: () => apiClient.get('/api/wishlist/'),
    addWishlist: (courseId) => apiClient.post('/api/wishlist/', { course_id: courseId }),
    removeWishlist: (courseId) => apiClient.delete('/api/wishlist/', { data: { course_id: courseId } }),
    reviews: (courseId) => apiClient.get(`/api/courses/${courseId}/reviews/`),
    saveReview: (courseId, data) => apiClient.post(`/api/courses/${courseId}/reviews/`, data),
    certificates: () => apiClient.get('/api/certificates/'),
    issueCertificate: (courseId) => apiClient.post(`/api/courses/${courseId}/certificates/issue/`),
    goals: () => apiClient.get('/api/goals/'),
    createGoal: (data) => apiClient.post('/api/goals/', data),
    updateGoal: (id, data) => apiClient.patch(`/api/goals/${id}/`, data),
    deleteGoal: (id) => apiClient.delete(`/api/goals/${id}/`),
    continueWatching: () => apiClient.get('/api/continue-watching/'),
    searchNotes: (q) => apiClient.get('/api/notes/search/', { params: { q } }),
}

export const discussionApi = {
    list: (courseId) => apiClient.get(`/api/courses/${courseId}/discussions/`),
    create: (courseId, data) => apiClient.post(`/api/courses/${courseId}/discussions/`, data),
    replies: (discussionId) => apiClient.get(`/api/discussions/${discussionId}/replies/`),
}

export const reportApi = {
    list: () => apiClient.get('/api/reports/'),
    create: (data) => apiClient.post('/api/reports/', data),
    update: (id, data) => apiClient.patch(`/api/reports/${id}/`, data),
}

export const instructorManageApi = {
    dashboard: () => apiClient.get('/api/instructor/dashboard/'),
    students: (params) => apiClient.get('/api/instructor/students/', { params }),
    notifyAtRisk: (enrollmentId, data) => apiClient.post(`/api/instructor/enrollments/${enrollmentId}/notify-at-risk/`, data),
}
