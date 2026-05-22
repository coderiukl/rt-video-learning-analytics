from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import JsonResponse

try:
    from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
except ImportError:
    SpectacularAPIView = None
    SpectacularSwaggerView = None

urlpatterns = [
    path('health/', lambda request: JsonResponse({"status": "ok"}), name='health'),
    path('', include('django_prometheus.urls')),
    path('admin/', admin.site.urls),
    path('api/auth/', include("users.urls")),
    path("api/", include("api.urls")),
    path("accounts/", include("allauth.urls")),

    path("api/courses/", include("courses.urls")),
    path("api/videos/", include("videos.urls")),
    path("api/analytics/", include("analytics.urls")),
]

if SpectacularAPIView and SpectacularSwaggerView:
    urlpatterns += [
        path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
        path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    ]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
