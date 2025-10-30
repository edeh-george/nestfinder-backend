import os
from enum import Enum
from logging import getLogger
from typing import Optional, Union
from urllib.parse import unquote, urlencode, urlparse

from cryptography.fernet import Fernet
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.contrib.sessions.backends.db import SessionStore
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes
from django.utils.html import strip_tags
from dotenv import load_dotenv
from rest_framework import status
from rest_framework.response import Response

from userauth.tasks import mail_message

from .check_celery import CeleryHealthChecker
from .safe_key import generate_safe_key

load_dotenv()
logger = getLogger("backend")
User = get_user_model()
session = SessionStore()
session_key = None

value = generate_safe_key()
cipher = Fernet(force_bytes(value))


class MailType(Enum):
    """Enumeration for different mail types."""

    PASSWORD_RESET = "password_reset"
    DELETE_ACCOUNT = "delete_account"
    EMAIL_VERIFICATION = "email_verification"
    PASSWORD_RESET_SUCCESS = "password_reset_success"
    COMPANY_INVITE = "company_invite"

    @property
    def template_name(self) -> str:
        """Get the template filename for this mail type."""
        return f"{self.value}.html"

    @property
    def subject(self) -> str:
        """Get the subject line for this mail type."""
        return " ".join(self.value.split("_")).title()

    def get_url_path(self, token: str, encoded_data: str) -> str:
        """Get the URL path for this mail type.
        Note: Password reset URL is same for password_reset_success,
        This enables user to retrieve their account for unauthorized
        password reset
        """

        if settings.FRONTEND_URL:
            params = urlencode({"token": token, "safe": encoded_data})
            return f"/login?{params}"
        url_patterns = {
            self.PASSWORD_RESET: f"/auth/resetpassword/{params}",
            self.DELETE_ACCOUNT: f"/delete-account/{params}",
            self.EMAIL_VERIFICATION: f"/auth/verify/{params}",
            self.PASSWORD_RESET_SUCCESS: f"/auth/resetpassword/{params}",
        }
        return url_patterns[self]


class EmailServiceError(Exception):
    """Custom exception for email service errors."""

    def __init__(self, message):
        super().__init__(message)


class EmailService:
    """Service class for handling email operations with Celery fallback."""

    def __init__(self, force_sync: bool = False):
        """
        Initialize EmailService.

        Args:
            force_sync: If True, always send emails synchronously
        """
        self.from_email = self._get_host_email()
        self.force_sync = force_sync
        self.celery_checker = CeleryHealthChecker()

    def _get_host_email(self) -> str:
        """Get the from email address from environment variables."""
        from_email = os.environ.get("EMAIL_HOST_USER")
        if not from_email:
            raise EmailServiceError("EMAIL_HOST_USER not set in environment variables")
        return from_email

    def _delete_user_from_db(email) -> None:
        """Delete user from database based on email."""
        try:
            user = User.objects.get(email=email)
            user.delete()
            logger.info(f"Deleted user with email {email} due to email send failure")
        except User.DoesNotExist:
            logger.warning(f"User with email {email} does not exist for deletion")

    def _send_email_sync(
        self, subject: str, message: str, recipient_email: str, html_message: str = None
    ) -> bool:
        """
        Send email synchronously using Django's built-in send_mail.

        Args:
            subject: Email subject
            message: Plain text message
            recipient_email: Recipient's email address
            html_message: HTML message (optional)

        Returns:
            bool: True if email was sent successfully
        """
        try:
            result = send_mail(
                subject=subject,
                message=message,
                from_email=self.from_email,
                recipient_list=[recipient_email],
                html_message=html_message,
                fail_silently=False,
            )
            logger.info(f"Email sent synchronously to {recipient_email}")
            return result > 0

        except Exception as e:
            logger.error(f"Error sending email synchronously: {str(e)}")

            try:
                if not self.force_sync:
                    logger.info("Falling back to asynchronous email sending via Celery")
                    return self._send_email_async(
                        subject, message, recipient_email, html_message
                    )
            except EmailServiceError:
                logger.error(
                    "Error sending email asynchronously during "
                    "fallback deleting user from database"
                )
                self._delete_user_from_db(recipient_email)
                return False

            raise EmailServiceError("Failed to send email synchronously")

    def _send_email_async(
        self, subject: str, message: str, recipient_email: str, html_message: str = None
    ) -> bool:
        """
        Send email asynchronously using Celery.

        Args:
            subject: Email subject
            message: Plain text message
            recipient_email: Recipient's email address
            html_message: HTML message (optional)

        Returns:
            bool: True if email was queued successfully
        """
        try:
            task_result = mail_message.apply_async(
                args=[subject, message, self.from_email, recipient_email, html_message]
            )
            logger.info(
                f"Email queued for {recipient_email}, task_id: {task_result.id}"
            )
            return True

        except Exception as e:
            logger.error(f"Error queuing email: {str(e)}")
            raise EmailServiceError(f"Failed to queue email: {str(e)}")

    def _should_use_celery(self) -> bool:
        """
        Determine whether to use Celery or send synchronously.

        Returns:
            bool: True if should use Celery, False for synchronous sending
        """
        if self.force_sync:
            logger.debug("Forced synchronous email sending")
            return False

        if not self.celery_checker.is_celery_ready():
            logger.warning(
                "Celery not available, falling back to synchronous email sending"
            )
            return False

        return True

    def _get_base_uri(self, request) -> str:
        """Get the base URI for generating verification links."""
        if settings.FRONTEND_URL:
            return settings.FRONTEND_URL
        client_domain = self.get_client_domain(request)
        if client_domain:
            parsed_uri = client_domain
        else:
            parsed_uri = urlparse(request.build_absolute_uri())

        return f"{parsed_uri.scheme}://{parsed_uri.netloc}"

    def _generate_verification_link(
        self,
        request,
        verification_token: str,
        encrypted_data: Union[str, bytes],
        mail_type: MailType,
    ) -> str:
        """Generate verification link for the given mail type."""
        base_uri = self._get_base_uri(request)

        if isinstance(encrypted_data, bytes):
            encoded_data = encrypted_data.decode()
        else:
            encoded_data = encrypted_data

        url_path = mail_type.get_url_path(verification_token, encoded_data)
        return f"{base_uri}{url_path}"

    def _prepare_email_content(
        self, user, verification_link: str, mail_type: MailType, kwargs
    ) -> tuple[str, str, str]:
        """Prepare email content (subject, plain text, HTML)."""
        try:
            context = {
                "username": user.first_name or user.username,
                "link": verification_link,
                **(kwargs or {}),
            }

            html_message = render_to_string(mail_type.template_name, context)
            plain_message = strip_tags(html_message)
            subject = mail_type.subject

            return subject, plain_message, html_message

        except Exception as e:
            logger.error(f"Error preparing email content: {str(e)}")
            raise EmailServiceError(f"Failed to prepare email content: {str(e)}")

    def get_client_domain(self, request) -> Optional[str]:
        """Extract the client domain from request headers."""
        origin = request.headers.get("Origin")
        if origin:
            return urlparse(origin)

        referer = request.headers.get("Referer")
        if referer:
            return urlparse(referer)

        return None

    def send_verification_email(
        self, request, user, mail_type: Union[str, MailType], kwargs
    ) -> Union[Response, str]:
        """
        Send verification email to the user with automatic Celery fallback.

        Args:
            request: The HTTP request object
            user: The user to send email to
            mail_type: Type of email to send

        Returns:
            Verification link string on success, or Response object on error
        """
        try:
            # Convert string to enum if necessary
            if isinstance(mail_type, str):
                try:
                    mail_type = MailType(mail_type)
                except ValueError:
                    logger.error(f"Invalid mail_type: {mail_type}")
                    return Response(
                        {"detail": f"Invalid mail type: {mail_type}"}, status=400
                    )
            verification_token = default_token_generator.make_token(user)
            encrypted_data = cipher.encrypt(force_bytes(user.pk))
            verification_link = self._generate_verification_link(
                request, verification_token, encrypted_data, mail_type
            )
            subject, plain_message, html_message = self._prepare_email_content(
                user, verification_link, mail_type, kwargs
            )
            if not html_message:
                return Response(
                    data={"message": "Message construction failed"}
                )
            if self._should_use_celery():
                self._send_email_async(subject, plain_message, user.email, html_message)
                logger.info(
                    f"Email queued via Celery for {user.email}, type: {mail_type.value}"
                )
            else:
                self._send_email_sync(subject, plain_message, user.email, html_message)
                logger.info(
                    f"Email sent synchronously to {user.email}, type: {mail_type.value}"
                )

            return verification_link

        except EmailServiceError as e:
            logger.error(f"EmailService error: {str(e)}")
            if isinstance(e, Response):
                return e
        except Exception as e:
            logger.error(f"Unexpected error sending email: {str(e)}")
            if isinstance(e, Response):
                return e
            return Response(
                {"detail": "Failed to send email", "error": str(e)}, status=500
            )


def send_email(request, user, mail_type, kwargs) -> Union[Response, str, None]:
    """

    Args:
        request: The HTTP request object
        user: The currently logged in user
        mail_type: The mail_type
        kwargs: Dict containig extra info for template context

    Returns:
        Response object on error, verification link string on success
    """
    email_service = EmailService()
    mail_type = MailType(mail_type)

    if not mail_type:
        logger.error("mail_type not provided in kwargs")
        return Response({"detail": "mail_type is required"}, status=400)

    return email_service.send_verification_email(request, user, mail_type, kwargs)


def verify_token(token: str, safe: str):
    """
    Verifies the token.

    Args:
        token: The token object to be verified
        safe: A cryprographically signed string used to obtain the user ID

    Returns:
        response: An instance of rest framework Response object if there was an error sending mail
        user: An instance of the default user model if token was verified
    """
    try:
        byte_user = unquote(safe)
        token = unquote(token)
        user_id = decrypt_token(byte_user)
        user = get_user(user_id)
        match = default_token_generator.check_token(user, token)
        if match:
            return user

        return Response({"error": "Invalid token"}, status=status.HTTP_400_BAD_REQUEST)

    except User.DoesNotExist as e:
        return Response(
            {"error": str(e)}, status=status.HTTP_400_BAD_REQUEST
        )
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
