from logging import getLogger

from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from django.core.validators import RegexValidator
from django.db import models
from django.utils import timezone
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from .models import generate_username

logger = getLogger("backend")

User = get_user_model()


class PasswordField(serializers.CharField):
    def __init__(self, **kwargs):
        # Set write_only to True by default
        kwargs["write_only"] = True
        super().__init__(**kwargs)


PasswordValidator = RegexValidator(
    regex=r"^.{7,}$",
    message="Password must be greater than 7 characters and cannot be empty",
    code="invalid_password",
)


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        exclude = [
            "id",
            "is_superuser",
            "password",
            "is_staff",
            "email_verified",
            "groups",
            "user_permissions",
        ]


class UserEmailVerificationSerializer(serializers.Serializer):
    pass


class UserSignUpSerializer(serializers.Serializer):

    class Gender(models.TextChoices):
        MALE = "M", "Male"
        FEMALE = "F", "Female"

    first_name = serializers.CharField(max_length=255, required=True)
    last_name = serializers.CharField(max_length=255, required=True)
    email = serializers.EmailField(required=True)
    gender = serializers.ChoiceField(choices=Gender, default="M")
    phone_number = serializers.CharField(
        max_length=15, required=False, allow_blank=True
    )
    password = PasswordField(required=True, validators=[PasswordValidator])
    password_confirm = PasswordField(required=True, validators=[PasswordValidator])
    has_accepted_terms = serializers.BooleanField(required=True)
    exam_type = serializers.CharField(max_length=25, required=False, allow_blank=True)

    def _validate_password(self, attrs):
        if attrs["password"] != attrs["password_confirm"]:
            raise serializers.ValidationError("Passwords don't match")
        attrs.pop("password_confirm")
        return attrs

    def _check_existing_email(self, attrs):
        email = attrs.get("email")
        if User.objects.filter(email=email).exists():
            raise serializers.ValidationError("Email is already in use")
        return attrs

    def validate(self, attrs):

        self._validate_password(attrs)
        self._check_existing_email(attrs)
        attrs["is_active"] = False

        attrs["username"] = generate_username(
            " ".join([attrs["first_name"], attrs["last_name"]])
        )

        return attrs

    def create(self, validated_data):
        """Created the user instance from the validated data

        Args:
            validated_data (dict): Dictionary containing user
            input on signup as well as process fields

        Returns:
            UserModel: Returns the instance of the user model
            created.
        """
        phone_number = validated_data.pop("phone_number", "")
        has_accepted_terms = validated_data.pop("has_accepted_terms", False)
        exam_type = validated_data.pop("exam_type", "")

        user = User.objects.create_user(**validated_data)

        if phone_number or exam_type or has_accepted_terms:
            profile = user.profile
            if phone_number:
                profile.phone_number = phone_number
            if exam_type:
                profile.exam_type = exam_type
            if has_accepted_terms:
                profile.has_accepted_terms = has_accepted_terms
                profile.accepted_terms_version = "1.0"
                profile.accepted_terms_date = timezone.now()
            profile.save()
        return user

    def update(self, instance, validated_data):

        field = list(validated_data.keys())[0]
        setattr(instance, field, make_password(validated_data[field]))
        instance.save(force_update=True, update_fields=validated_data.keys())

        return instance


class UserPasswordResetSerializer(serializers.Serializer):
    email = serializers.EmailField(required=False)


class TokenVerificationSerializer(serializers.Serializer):
    token = serializers.CharField()
    safe = serializers.CharField()


class UserNewPasswordResetSerializer(serializers.Serializer):
    password = PasswordField(validators=[PasswordValidator])
    password_confirm = PasswordField(validators=[PasswordValidator])

    def validate(self, attrs):
        if attrs["password"] != attrs["password_confirm"]:
            raise ValidationError(detail="Passwords don't match")
        del attrs["password_confirm"]
        return attrs

    def update(self, instance, validated_data):
        field = list(validated_data.keys())[0]
        setattr(instance, field, make_password(validated_data[field]))
        instance.save(force_update=True, update_fields=validated_data.keys())
        return instance

    def create(self, validated_data):
        return User()


class UserLogoutSerializer(serializers.Serializer):
    pass


class GoogleUrlSerializer(serializers.Serializer):
    url = serializers.URLField()


class ReactivateDeactivateUserSerializer(serializers.Serializer):
    action = serializers.ChoiceField(
        choices=[("deactivate", "Deactivate"), ("reactivate", "Reactivate")],
        help_text="Choose 'deactivate' to deactivate user account or 'reactivate' to reactivate it.",
    )


class GoogleAuthCompleteSerializer(serializers.Serializer):
    access_token = serializers.CharField()


class UserDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        exclude = [
            "id",
            "is_superuser",
            "password",
            "is_staff",
            "email_verified",
            "groups",
            "user_permissions",
        ]
