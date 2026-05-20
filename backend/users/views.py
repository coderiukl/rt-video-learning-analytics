import random
import string
from datetime import timedelta
from django.shortcuts import render
from django.core.cache import cache
from django.core.mail import send_mail
from django.contrib.auth import login, logout
from django.contrib.auth.hashers import check_password
from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError

from .models import InstructorProfile, User
from .serializers import (
    InstructorProfileSerializer,
    LoginSerializer,
    RegisterSerializer,
    UserProfileUpdateSerializer,
    UserSerializer,
)

# Create your views here.
def get_tokens_for_user(user):
    """Tạo cặp JWT access + refresh token cho user"""
    refresh = RefreshToken.for_user(user)
    return {
        "access": str(refresh.access_token),
        "refresh": str(refresh),
    }

def update_last_login(user):
    now = timezone.now()
    user.last_login = now
    user.last_login_at = now
    user.save(update_fields=["last_login", "last_login_at"])

# Register
class RegisterView(APIView):
    """
    POST /api/auth/register/
    Body: {email, full_name, password, role}
    """

    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        user = serializer.save()
        tokens = get_tokens_for_user(user)

        return Response({
            "message": "Đăng ký thành công.",
            "user": UserSerializer(user).data,
            "tokens": tokens,
        }, status=status.HTTP_201_CREATED)
    
# JWT AUTH
class JWTLoginView(APIView):
    """
    POST /api/auth/jwt-login/
    Body: {email, password}
    Returns: {access, refresh, user}
    """
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        user = serializer.validated_data['user']
        update_last_login(user)
        
        return Response({
            "message": "Đăng nhập JWT thành công.",
            "user": UserSerializer(user).data,
            "tokens": get_tokens_for_user(user),
        })
    
class JWTLogutView(APIView):
    """
    POST /api/auth/jwt/logout/
    Header: Authorization: Bearer <access_token>
    Body:   { refresh: "<refresh_token>" }
    Blacklist refresh token để vô hiệu hóa hoàn toàn.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        refresh_token = request.data.get("refresh")
        if not refresh_token:
            return Response({"error": "Thiếu refresh token."}, status=status.HTTP_400_BAD_REQUEST)
        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
        except TokenError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
        return Response({"message": "Đăng xuất JWT thành công"})
    
class JWTRefreshView(APIView):
    """
    POST /api/auth/jwt/refresh/
    Body: { refresh: "<refresh_token>" }
    Returns: { access: "<new_access_token>" }
    """
    permission_classes = [AllowAny]
 
    def post(self, request):
        refresh_token = request.data.get("refresh")
        if not refresh_token:
            return Response({"error": "Thiếu refresh token."}, status=status.HTTP_400_BAD_REQUEST)
        try:
            token  = RefreshToken(refresh_token)
            return Response({"access": str(token.access_token)})
        except TokenError as e:
            return Response({"error": str(e)}, status=status.HTTP_401_UNAUTHORIZED)
        
class MeView(APIView):
    """
    GET /api/auth/me/
    Dùng được với cả JWT lẫn Session.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(UserSerializer(request.user).data)

    def patch(self, request):
        serializer = UserProfileUpdateSerializer(request.user, data=request.data, partial=True)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        user = serializer.save()
        return Response(UserSerializer(user).data)


class InstructorProfileApplyView(APIView):
    """
    POST /api/auth/instructor-profile/
    Body: { headline, bio, profile_url, expertise }
    Creates or updates a pending instructor profile. Admin approval is required.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            profile = request.user.instructor_profile
        except InstructorProfile.DoesNotExist:
            return Response({"status": "none"})

        return Response({
            "status": UserSerializer(request.user).data["instructor_status"],
            "profile": InstructorProfileSerializer(profile).data,
        })

    def post(self, request):
        try:
            profile = request.user.instructor_profile
        except InstructorProfile.DoesNotExist:
            profile = None

        if (
            profile
            and request.user.role == User.Role.INSTRUCTOR
            and profile.is_verified
            and profile.is_active
        ):
            return Response(
                {"error": "Hồ sơ giảng viên đã được duyệt."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        created = profile is None
        serializer = InstructorProfileSerializer(profile, data=request.data, partial=bool(profile))
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        profile = serializer.save(user=request.user, is_verified=False, is_active=False)
        return Response({
            "message": "Hồ sơ giảng viên đã được gửi. Vui lòng chờ admin duyệt.",
            "status": "pending",
            "profile": InstructorProfileSerializer(profile).data,
        }, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)

# Change Password & Forget Password
def generate_otp(length=6):
    return "".join(random.choices(string.digits, k=length))

def get_otp_cache_key(email):
    return f"otp_reset_{email}"

class ChangePasswordView(APIView):
    """
    POST /api/auth/change-password/
    Header: Authorization: Bearer <access_token>
    Body: { old_password, new_password }
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        old_password = request.data.get('old_password')
        new_password = request.data.get('new_password')

        # Validate input
        if not old_password or not new_password:
            return Response({
                "error": "Vui lòng nhập đủ old_password và new_password."
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Check Old Password
        if not user.check_password(old_password):
            return Response(
                {"error": "Mật khẩu cũ không đúng"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check Old and New is the same password
        if old_password == new_password:
            return Response(
                {"error": "Mật khẩu mới không được trùng mật khẩu cũ."},
                status=status.HTTP_400_BAD_REQUEST
            )


        # Check length password
        if len(new_password) < 8:
            return Response(
                {"error": "Mật khẩu mới phải có ít nhất 8 ký tự."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        user.set_password(new_password)
        user.save()

        return Response({"message": "Đổi mật khẩu thành công."})
    
class ForgotPasswordSendOTPView(APIView):
    """
    POST /api/auth/forgot-password/send-otp/
    Body: { email }
    Gửi mã OTP 6 số về email, hết hạn sau 5 phút.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get("email", '').strip()

        if not email:
            return Response(
                {"error": "Vui lòng nhập email."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check email exist
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({"message": "Nếu email tồn tại, OTP đã được gửi."})
        
        # Generate OTP and save to cache (5 minutes)
        otp = generate_otp()
        cache.set(get_otp_cache_key(email), otp, timeout=600)

        # Send Email
        send_mail(
            subject="Mã OTP đặt lại mật khẩu",
            message=f"""
Xin chào {user.full_name},

Mã OTP của bạn là: {otp},

Mã này có hiệu lực trong 5 phút. Vui lòng không chia sẻ mã này với bất kì ai.

Nếu bạn không yêu cầu đặt lại mật khẩu, hãy bỏ qua email này.
            """,
            from_email=None,
            recipient_list=[email],
        )

        return Response({"message": "Nếu email tồn tại, OTP đã được gửi."})
    
class ForgotPasswordVerifyOTPView(APIView):
    """
    POST /api/auth/forgot-password/verify-otp/
    Body: { email, otp }
    Trả về reset_token nếu OTP đúng.
    """

    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get("email", "").strip()
        otp = request.data.get("otp", "").strip()

        if not email and not otp:
            return Response(
                {"error": "Vui lòng nhập email và otp."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        cached_otp = cache.get(get_otp_cache_key(email))

        if not cached_otp:
            return Response(
                {"error": "OTP đã hết hạn. Vui lòng yêu cầu lại."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if cached_otp != otp:
            return Response(
                {"error": "OTP không đúng"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # OTP is correct -> Delete OTP, generate reset_token (10 minutes)
        cache.delete(get_otp_cache_key(email))
        reset_token = generate_otp(32) # Token dài hơn để bảo mật
        cache.set(f"reset_token_{email}", reset_token, timeout=1200)

        return Response({
            "message": "OTP hợp lệ",
            "reset_token": reset_token,
        })
    
class ForgotPasswordResetView(APIView):
    """
    POST /api/auth/forgot-password/reset/
    Body: { email, reset_token, new_password }
    """

    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get("email", "").strip()
        reset_token = request.data.get("reset_token", "").strip()
        new_password = request.data.get("new_password", "")

        if not email or not reset_token or not new_password:
            return Response(
                {"error": "Vui lòng nhập đủ email, reset_token và new_password"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if len(new_password) < 8:
            return Response(
                {"error": "Mật khẩu mới phải có ít nhất 8 ký tự."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check reset_token
        cached_token = cache.get(f"reset_token_{email}")
        if not cached_token or cached_token != reset_token:
            return Response(
                {"error": "Reset token không hợp lệ hoặc đã hết hạn."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response(
                {"error": "Không tìm thấy tài khoản."},
                status=status.HTTP_404_NOT_FOUND
            )

        user.set_password(new_password)
        user.save()

        # Delete Token after use
        cache.delete(f"reset_token_{email}")

        return Response({"message": "Đặt lại mật khẩu thành công. Vui lòng đăng nhập lại."})
    
