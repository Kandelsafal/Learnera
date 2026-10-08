from rest_framework import serializers
from .models import User
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password


#Read Data from the Model
class UserSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = [
             "id",
            "first_name",
            "last_name",
            "email",
            "phn_number",
            "is_email_verified",
            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "id",
            "email",
            "is_email_verified",
            "created_at",
            "updated_at",
        ]

class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only = True,
        min_length = 8
    )

    class Meta:
        model = User
        fields = [
            "id",
            "first_name",
            "last_name",
            "email",
            "phn_number",
            "password",
        ]
        read_only_fields = [
            "id"
        ]
#Separate Password from other user Field
    def create(self, validated_data):
        password = validated_data.pop("password")

        user = User.objects.create_user(
            password = password,
            **validated_data
        )
        return user

class UserLoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(
        write_only = True,
        min_length = 8
    )

    def validate(self, attrs):
        email = attrs.get("email")
        password = attrs.get("password")

        user =  authenticate(email = email, password = password)

        if user is None:
            raise serializers.ValidationError(
                "Invalid Email or Password"
            )

        if not user.is_email_verified:
            raise serializers.ValidationError(
                "User Email is not verified."
            )
        

        if not user.is_active:
             raise serializers.ValidationError(
                "User account is inactive."
            )

        attrs["user"] = user
        return attrs

class ChangePasswordSerializer(serializers.Serializer):
    current_password = serializers.CharField(
        write_only = True,
        min_length = 8
    )
    new_password = serializers.CharField(
            write_only = True,
            min_length = 8
        )

    def validate(self, attrs):
        user = self.context["request"].user

        current_password = attrs["current_password"]
        new_password = attrs["new_password"]

        if not user.check_password(current_password):
            raise serializers.ValidationError(
                 "Current password is incorrect."
            )
        validate_password(
            new_password,
            user = user
        )
        return attrs


class EmailVerificationSerializer(serializers.Serializer):

    token = serializers.CharField(
        write_only=True
    )