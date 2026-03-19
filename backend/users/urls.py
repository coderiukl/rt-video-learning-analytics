from django.urls import path
from .views import (
    RegisterView,
    JWTLoginView, JWTLogutView, JWTRefreshView,
    MeView
)

urlpatterns = [
    # Register
    path('register/', RegisterView.as_view(), name='auth-register'),

    #JWT
    path('login/', JWTLoginView.as_view(), name='login'),
    path('logout/', JWTLogutView.as_view(), name='logout'),
    path('refresh/', JWTRefreshView.as_view(), name='refresh'),

    #Profile
    path('me/', MeView.as_view(), name='auth-me'),
]