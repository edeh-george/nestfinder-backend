from typing import Any
from django.db import models
from django.contrib.auth.models import AbstractUser, UserManager
from django.utils.translation import gettext_lazy as _
from functools import wraps


def add_email_verified_field(func):
    """
    This decorator add the extra fields that need to be modified
    when creating a super user without modifing other features of
    Django create_superuser function for the UserManager.
    """
    @wraps(func)
    def wrapper(self, username, email=None, password=None, **extra_fields):
        # Add email_verified to extra_fields
        extra_fields.setdefault("email_verified", True)
        return func(self, username, email, password, **extra_fields)
    return wrapper


class CustomUserManager(UserManager):

    @add_email_verified_field
    def create_superuser(self, username: str, email: str | None, password: str | None, **extra_fields: Any) -> Any:
        return super().create_superuser(username, email, password, **extra_fields)
    

# Create your models here.
class UserModel(AbstractUser):
    email = models.EmailField(_("email address"), unique=True, blank=True)
    email_verified = models.BooleanField(default=False)
    is_landlord = models.BooleanField(default=False)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    objects = CustomUserManager()