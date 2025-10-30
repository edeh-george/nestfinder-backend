import random
from functools import wraps
from typing import Any
from utils.model_abstracts import UUIDModelAbstract

from django.contrib.auth.models import AbstractUser, UserManager
from django.db import models
from django.utils.translation import gettext_lazy as _


def generate_username(value):
    value = value.lower().replace(" ", ".")
    unique_id = str(random.randint(1, 99))
    counter = 1
    while UserModel.objects.filter(username=value):
        value = f"{value.lower().replace(' ','.')}.{unique_id}"
        counter += 1

    return value


def add_email_verified_field(func):
    @wraps(func)
    def wrapper(self, username, email=None, password=None, **extra_fields):
        # Add email_verified to extra_fields
        extra_fields.setdefault("email_verified", True)
        return func(self, username, email, password, **extra_fields)

    return wrapper


class CustomUserManager(UserManager):

    @add_email_verified_field
    def create_superuser(
        self,
        username: str,
        email: str | None,
        password: str | None,
        **extra_fields: Any
    ) -> Any:
        return super().create_superuser(username, email, password, **extra_fields)


class UserModel(AbstractUser,
                 UUIDModelAbstract):
    email = models.EmailField(_("email address"), unique=True, blank=True)
    email_verified = models.BooleanField(default=False)
    is_landlord = models.BooleanField(default=False)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    objects = CustomUserManager()

    def save(self, *args, **kwargs):
        if not self.username:
            self.username = generate_username(
                self.fullname
                if self.fullname
                else " ".join([self.first_name, self.last_name])
            )

        if not self.fullname:
            if hasattr(self, "first_name") or hasattr(self, "last_name"):
                self.fullname = (
                    " ".join([self.first_name, self.last_name]).strip().title()
                )
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return self.email
