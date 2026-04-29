from django.urls import path

from .views import (
    AdminBehaviorAnalyticsView,
    CourseBehaviorAnalyticsView,
    InstructorBehaviorAnalyticsView,
    LearningEventCreateView,
)


urlpatterns = [
    path("events/", LearningEventCreateView.as_view(), name="learning-event-create"),
    path("instructor/behavior/", InstructorBehaviorAnalyticsView.as_view(), name="instructor-behavior"),
    path("courses/<int:course_id>/behavior/", CourseBehaviorAnalyticsView.as_view(), name="course-behavior"),
    path("admin/behavior/", AdminBehaviorAnalyticsView.as_view(), name="admin-behavior"),
]
