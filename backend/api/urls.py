from django.urls import path
from .views import (
    AdminAuditLogView, AdminCourseListView, AdminCourseModerationView, AdminDashboardView,
    AdminInstructorApprovalView, AdminInstructorRejectView, AdminSystemSettingView,
    AdminUserListView, AdminUserManageView, AdminUserResetPasswordView,
    CertificateListIssueView, ContinueWatchingView, CourseReviewListCreateView,
    DiscussionListCreateView, DiscussionRepliesView, InstructorDashboardView,
    InstructorNotifyAtRiskView, InstructorStudentsView, LearningGoalManageView,
    LearningGoalView, NotificationListView, NotificationReadView, ReportListCreateView,
    ReportManageView, StudentNotesSearchView, WishlistView,
)

urlpatterns = [
    path("notifications/", NotificationListView.as_view(), name="notifications"),
    path("notifications/read/", NotificationReadView.as_view(), name="notifications-read-all"),
    path("notifications/<int:notification_id>/read/", NotificationReadView.as_view(), name="notification-read"),

    path("admin/dashboard/", AdminDashboardView.as_view(), name="admin-dashboard"),
    path("admin/users/", AdminUserListView.as_view(), name="admin-users"),
    path("admin/users/<uuid:user_id>/", AdminUserManageView.as_view(), name="admin-user-manage"),
    path("admin/users/<uuid:user_id>/reset-password/", AdminUserResetPasswordView.as_view(), name="admin-user-reset-password"),
    path("admin/instructors/<uuid:user_id>/approve/", AdminInstructorApprovalView.as_view(), name="admin-instructor-approve"),
    path("admin/instructors/<uuid:user_id>/reject/", AdminInstructorRejectView.as_view(), name="admin-instructor-reject"),
    path("admin/courses/", AdminCourseListView.as_view(), name="admin-courses"),
    path("admin/courses/<int:course_id>/moderate/", AdminCourseModerationView.as_view(), name="admin-course-moderate"),
    path("admin/audit-logs/", AdminAuditLogView.as_view(), name="admin-audit-logs"),
    path("admin/settings/", AdminSystemSettingView.as_view(), name="admin-settings"),

    path("wishlist/", WishlistView.as_view(), name="wishlist"),
    path("courses/<int:course_id>/reviews/", CourseReviewListCreateView.as_view(), name="course-reviews"),
    path("certificates/", CertificateListIssueView.as_view(), name="certificates"),
    path("courses/<int:course_id>/certificates/issue/", CertificateListIssueView.as_view(), name="certificate-issue"),
    path("goals/", LearningGoalView.as_view(), name="learning-goals"),
    path("goals/<int:goal_id>/", LearningGoalManageView.as_view(), name="learning-goal-manage"),
    path("continue-watching/", ContinueWatchingView.as_view(), name="continue-watching"),
    path("notes/search/", StudentNotesSearchView.as_view(), name="notes-search"),

    path("courses/<int:course_id>/discussions/", DiscussionListCreateView.as_view(), name="course-discussions"),
    path("discussions/<int:discussion_id>/replies/", DiscussionRepliesView.as_view(), name="discussion-replies"),
    path("reports/", ReportListCreateView.as_view(), name="reports"),
    path("reports/<int:report_id>/", ReportManageView.as_view(), name="report-manage"),

    path("instructor/dashboard/", InstructorDashboardView.as_view(), name="instructor-dashboard"),
    path("instructor/students/", InstructorStudentsView.as_view(), name="instructor-students"),
    path("instructor/enrollments/<int:enrollment_id>/notify-at-risk/", InstructorNotifyAtRiskView.as_view(), name="instructor-notify-at-risk"),
]

