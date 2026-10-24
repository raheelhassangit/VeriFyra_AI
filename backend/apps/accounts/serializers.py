from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from .models import User


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, trim_whitespace=False, style={"input_type": "password"})

    class Meta:
        model = User
        fields = ("id", "email", "full_name", "role", "password")
        read_only_fields = ("id", "role")

    def to_internal_value(self, data):
        # Public registration can never choose a role, so reject the attempt loudly.
        if "role" in data:
            raise serializers.ValidationError({"role": "Role cannot be set during registration."})
        return super().to_internal_value(data)

    def validate_email(self, value):
        value = value.strip().lower()
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value

    def validate(self, attrs):
        validate_password(attrs["password"], user=User(email=attrs["email"], full_name=attrs.get("full_name", "")))
        return attrs

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)  # role defaults to PARTICIPANT


class MeSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "email", "full_name", "role", "date_joined")
        read_only_fields = ("id", "email", "role", "date_joined")


class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField()