from django.urls import path

from .views import (
    AdminBehaviorAnalyticsView,
    CourseBehaviorAnalyticsView,
    InstructorBehaviorAnalyticsView,
    LearningEventCreateView,
    AtRiskStudentsView,
    VideoHeatmapView,
    DropoutModelReloadView,
    DropoutModelStatusView,
    LearningStyleView,
    CourseRecommendationView,
    PersonalizedCourseRecommendationView,
)

urlpatterns = [
    path("events/", LearningEventCreateView.as_view(), name="learning-event-create"),
    path("instructor/behavior/", InstructorBehaviorAnalyticsView.as_view(), name="instructor-behavior"),
    path("courses/<int:course_id>/behavior/", CourseBehaviorAnalyticsView.as_view(), name="course-behavior"),
    path("courses/<int:course_id>/at-risk/", AtRiskStudentsView.as_view(), name="course-at-risk"),
    path("videos/<int:video_id>/heatmap/", VideoHeatmapView.as_view(), name="video-heatmap"),
    path("admin/behavior/", AdminBehaviorAnalyticsView.as_view(), name="admin-behavior"),
    # Dropout Prediction Model endpoints (training is offline via mlops/)
    path("dropout-model/reload/", DropoutModelReloadView.as_view(), name="dropout-model-reload"),
    path("dropout-model/status/", DropoutModelStatusView.as_view(), name="dropout-model-status"),
    path("courses/<int:course_id>/learning-styles/", LearningStyleView.as_view(), name="course-learning-styles"),
    path("courses/<int:course_id>/recommendations/", CourseRecommendationView.as_view(), name="course-recommendations"),
    path("courses/personalized-recommendations/", PersonalizedCourseRecommendationView.as_view(), name="course-personalized-recommendations"),
]
