import os
from typing import Union
from urllib.parse import unquote, urlparse

from cryptography.fernet import Fernet
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.contrib.sessions.backends.db import SessionStore
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes
from django.utils.html import strip_tags
from dotenv import load_dotenv
from rest_framework import status
from rest_framework.response import Response

from .safe_key import generate_safe_key

load_dotenv()


User = get_user_model()
session = SessionStore()
session_key = None

value = generate_safe_key()
cipher = Fernet(value)


def get_parsed_url_from_request(uri):
    return urlparse(uri)


def send_email(request, user, **kwargs) -> Union[Response, None]:

    # Generate verification url for the email
    verification_token = default_token_generator.make_token(user)
    encrypted_data = cipher.encrypt(force_bytes(user.pk))
    parsed_uri = get_parsed_url_from_request(request.build_absolute_uri())
    url_scheme = parsed_uri.scheme
    current_domain = parsed_uri.netloc
    if kwargs["mail_type"] == "password_reset":
        verification_link = f"{url_scheme}://{current_domain}/api/v1/password/reset/confirm/{verification_token}/{encrypted_data.decode()}"
    else:
        verification_link = f"{url_scheme}://{current_domain}/api/v1/verify/{verification_token}/{encrypted_data.decode()}"

    """Logic for sending mail alos sends mail as plain text incase html cannot be rendered"""
    html_message = render_to_string(
        f"{kwargs['mail_type']}.html",
        {"username": user.first_name, "link": verification_link},
    )
    plain_message = strip_tags(html_message)
    subject = (
        "Password Reset"
        if kwargs["mail_type"] == "password_reset"
        else "Verify your email"
    )
    from_email, to = os.environ.get("EMAIL_HOST_USER"), user.email
    msg = EmailMultiAlternatives(subject, plain_message, from_email, [to])
    msg.attach_alternative(html_message, "text/html")
    # try:
    #     msg.send()
    # except ValidationError as e:
    #     return Response(e.messages, status=status.HTTP_400_BAD_REQUEST)

    return verification_link


def verify_token(token: str, safe: str):
    try:
        byte_user = unquote(safe)
        user_id = decrypt_token(byte_user)
        user = get_user(user_id)
        match = default_token_generator.check_token(user, token)
        if match:
            return user

        return Response({"error": "Invalid token"}, status=status.HTTP_400_BAD_REQUEST)

    except User.DoesNotExist as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response(
            {"error": "An unexpected error occurred", "details": str(e)},
            status=status.HTTP_400_BAD_REQUEST,
        )


def decrypt_token(token: str) -> str:
    """Decrypts the token and returns the user ID."""
    try:
        user_id = cipher.decrypt(force_bytes(token))
        return user_id.decode("utf-8")
    except Exception as e:
        raise Exception("Token could not be decrypted") from e


def get_user(user_id: str):
    """Fetches the user based on the user ID."""
    return User.objects.get(pk=user_id)
