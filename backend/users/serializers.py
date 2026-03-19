from django.contrib.auth import authenticate
from rest_framework import serializers
from .models import User

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    role = serializers.ChoiceField(choices=["student", "instructor"], default="student")
    
    class Meta:
        model = User
        fields = ['email', 'full_name', 'password', 'role']

    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)

        # Tạo profile tương ứng
        from .models import StudentProfile, InstructorProfile
        if user.role == User.Role.STUDENT:
            StudentProfile.objects.create(user=user)
        elif user.role == User.Role.INSTRUCTOR:
            InstructorProfile.objects.create(user=user)
        return user
    
class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        user = authenticate(email=data["email"], password=data['password'])
        if not user:
            raise serializers.ValidationError("Email hoặc mật khẩu không đúng.")
        if not user.is_active:
            raise serializers.ValidationError("Tài khoản đã bị khóa.")
        data['user'] = user
        return data
    
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model  = User
        fields = ["user_id", "email", "full_name", "avatar_url", "role",
                  "is_email_verified", "created_at"]