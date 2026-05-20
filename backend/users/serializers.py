from django.contrib.auth import authenticate
from rest_framework import serializers

from .models import InstructorProfile, StudentProfile, User


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ["email", "full_name", "password"]

    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        StudentProfile.objects.create(user=user)
        return user


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        user = authenticate(email=data["email"], password=data["password"])
        if not user:
            raise serializers.ValidationError("Email hoặc mật khẩu không đúng.")
        if not user.is_active:
            raise serializers.ValidationError("Tài khoản đã bị khóa.")
        data["user"] = user
        return data


class UserSerializer(serializers.ModelSerializer):
    instructor_status = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "user_id", "email", "full_name", "avatar_url", "role",
            "is_staff", "is_superuser", "is_email_verified", "instructor_status",
            "last_login", "last_login_at", "created_at",
        ]

    def get_instructor_status(self, user):
        try:
            profile = user.instructor_profile
        except InstructorProfile.DoesNotExist:
            return "none"

        if user.role == User.Role.INSTRUCTOR and profile.is_verified and profile.is_active:
            return "approved"
        return "pending"


class UserProfileUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["full_name", "avatar_url"]

    def validate_full_name(self, value):
        value = (value or "").strip()
        if not value:
            raise serializers.ValidationError("Vui lòng nhập họ và tên.")
        return value


class InstructorProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = InstructorProfile
        fields = ["headline", "bio", "profile_url", "expertise", "is_verified", "is_active"]
        read_only_fields = ["is_verified", "is_active"]

    def validate_profile_url(self, value):
        value = (value or "").strip()
        if not value:
            raise serializers.ValidationError("Vui lòng nhập đường dẫn hồ sơ giảng viên.")
        return value
