from django.urls import path
from .views import (
    RegisterView,
    JWTLoginView, JWTLogutView, JWTRefreshView,
    ChangePasswordView, ForgotPasswordResetView, ForgotPasswordSendOTPView, ForgotPasswordVerifyOTPView,
    MeView,
)

urlpatterns = [
    # Register
    path('register/', RegisterView.as_view(), name='auth-register'),

    # JWT
    path('login/', JWTLoginView.as_view(), name='login'),
    path('logout/', JWTLogutView.as_view(), name='logout'),
    path('refresh/', JWTRefreshView.as_view(), name='refresh'),

    # Change Password
    path('change-password/', ChangePasswordView.as_view(), name='change-password'),
    
    # Forget Password
    path('forgot-password/send-otp/', ForgotPasswordSendOTPView.as_view(), name='forgot-send-otp'),
    path('forgot-password/verify-otp/', ForgotPasswordVerifyOTPView.as_view(), name='forgot-verify-otp'),
    path('forgot-password/reset/', ForgotPasswordResetView.as_view(), name='forgot-reset'),

    # Profile
    path('me/', MeView.as_view(), name='auth-me'),
]