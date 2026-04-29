from django.urls import path

from .views import (
    CourseVideoListCreateView,
    VideoManageView,
    VideoNoteListCreateView,
    VideoNoteManageView,
    VideoProgressView,
    VideoStreamView,
)


urlpatterns = [
    path("courses/<int:course_id>/", CourseVideoListCreateView.as_view(), name="course-videos"),
    path("<int:video_id>/progress/", VideoProgressView.as_view(), name="video-progress"),
    path("<int:video_id>/notes/", VideoNoteListCreateView.as_view(), name="video-notes"),
    path("notes/<int:note_id>/", VideoNoteManageView.as_view(), name="video-note-manage"),
    path("<int:video_id>/stream/", VideoStreamView.as_view(), name="video-stream"),
    path("<int:video_id>/", VideoManageView.as_view(), name="video-manage"),
]
