from django.shortcuts import render
from django.contrib.auth import login, logout
from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError

from .serializers import LoginSerializer, RegisterSerializer, UserSerializer

# Create your views here.
def get_tokens_for_user(user):
    """Tạo cặp JWT access + refresh token cho user"""
    refresh = RefreshToken.for_user(user)
    return {
        "access": str(refresh.access_token),
        "refresh": str(refresh),
    }

def update_last_login(user):
    user.last_login_at = timezone.now()
    user.save(update_fields=["last_login_at"])

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
    