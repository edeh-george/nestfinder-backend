from logging import getLogger
from urllib.parse import urlencode

from django.conf import settings
from django.contrib.auth import get_user_model, logout
from django.db import transaction
from django.middleware import csrf
from django.utils.crypto import get_random_string
from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_view
from rest_framework import generics, permissions, status, views
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework_simplejwt.exceptions import InvalidToken
from rest_framework_simplejwt.tokens import RefreshToken, Token
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from utils.send_mail import send_email, verify_token

from .serializers import (
    GoogleAuthCompleteSerializer,
    GoogleUrlSerializer,
    ReactivateDeactivateUserSerializer,
    TokenVerificationSerializer,
    UserDetailSerializer,
    UserEmailVerificationSerializer,
    UserLogoutSerializer,
    UserNewPasswordResetSerializer,
    UserPasswordResetSerializer,
    UserSignUpSerializer,
)

User = get_user_model()
logger = getLogger("backend")


class VerifyEmailView(generics.GenericAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = UserEmailVerificationSerializer
    queryset = User.objects.none()

    @extend_schema(tags=["authentication"])
    def post(self, request: Request, *args, **kwargs):
        try:
            request_data = {"safe": kwargs["safe"], "token": kwargs["token"]}
            serializer = TokenVerificationSerializer(data=request_data)
            serializer.is_valid(raise_exception=True)
            data = serializer.validated_data
            value = verify_token(**data)
            if isinstance(value, User):
                logger.info("Verification token verified")
                value.is_active = True
                value.email_verified = True
                value.save(force_update=True)
                return Response(
                    "User E-mail verified successfully",
                    status=status.HTTP_200_OK,
                )
            if isinstance(value, Response):
                return value

        except Exception as e:
            return Response(
                {"error": str(e)}, status=status.HTTP_400_BAD_REQUEST
            )


class CustomTokenObtainPairView(TokenObtainPairView):
    parser_classes = [JSONParser, FormParser, MultiPartParser]
    queryset = User.objects.none()

    @extend_schema(tags=["authentication"])
    def post(self, request: Request, *args, **kwargs) -> Response:
        try:

            email, password = request.data.get("email"), request.data.get("password")
            user = User.objects.filter(email=email).first()
            if not user:
                return Response(
                    {"error": "Error getting user details", "message": "Invalid Email"},
                    status=status.HTTP_401_UNAUTHORIZED,
                )
            if not user.check_password(password):
                return Response(
                    {
                        "error": "Error getting user details",
                        "message": "Invalid Password",
                    },
                    status=status.HTTP_401_UNAUTHORIZED,
                )
            if not user.is_active:
                return Response(
                    {
                        "error": "User account is not active. Contact admin to clarify",
                        "message": "Inactive account",
                    },
                    status=status.HTTP_401_UNAUTHORIZED,
                )

            response = super().post(request, *args, **kwargs)
            if response.status_code == status.HTTP_200_OK:
                email = request.data.get("email")
                user = User.objects.get(email=email)
                if not user.email_verified:
                    try:
                        link = send_email(
                            request=request,
                            user=user,
                            mail_type="email_verification",
                            kwargs={},
                        )
                        return Response(
                            {
                                "email": f"Sorry {user.username}, your email is not verified. "
                                + "Please kindly check your mail to verify your account",
                                "link": link,
                            },
                            status=status.HTTP_401_UNAUTHORIZED,
                        )
                    except Exception as e:
                        logger.error(f"Error sending email: {e}")
                        return Response(
                            {
                                "error": "Server didn't respond in time",
                                "message": str(e),
                            },
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        )

            if hasattr(request, "session"):
                request.session["access"] = response.data["access"]
                request.session["refresh"] = response.data["refresh"]
                request.session["_auth_user_id"] = str(user.pk)
            if request.query_params.get("remember_me"):
                request.session.set_expiry(0)

            csrf.get_token(request)
            response.data["is_authenticated"] = user.is_authenticated
            del response.data["refresh"]

            payload = {
                **response.data,
                "user": {"username": user.username, "email": user.email},
            }

            logger.info(f"response.data: {response.data}")
            return Response(
                data=payload,
                message="User successfully authenticated",
                status=response.status_code,
            )

        except Exception as e:
            return Response(
                data=str(e),
                message="Server error occurred",
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class CustomTokenRefreshView(TokenRefreshView):
    permission_classes = [permissions.AllowAny]
    parser_classes = [JSONParser, FormParser, MultiPartParser]

    queryset = User.objects.none()

    @extend_schema(tags=["authentication"])
    def post(self, request, *args, **kwargs):
        try:
            if hasattr(request, "session"):
                refresh_token = request.session.get("refresh")
                logger.debug(f"token: {refresh_token}")
                if not refresh_token:
                    return Response(
                        {"error": "Refresh token missing"},
                        status=status.HTTP_401_UNAUTHORIZED,
                    )

                """Modifies the request to contain the refresh token"""
                data = request.data.copy()
                data["refresh"] = refresh_token
                request._full_data = data
                response = super().post(request, *args, **kwargs)
                logger.debug(f"Refresh token response recieved status: {response.data}")
                request.session["access"] = response.data["access"]
                request.session["refresh"] = response.data["refresh"]
                del response.data["refresh"]

                return Response(
                    data=response.data, status=response.status_code
                )
        except InvalidToken:
            return Response(
                {"error": "Invalid token or token expired"},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        except Exception as e:
            return Response(
                {"error": str(e)}, status=status.HTTP_401_UNAUTHORIZED
            )


def generate_state(request, backend_name="google-oauth2"):
    state = get_random_string(32)
    request.session[f"{backend_name}_state"] = state

    return state


class GoogleLoginURLAPIView(generics.GenericAPIView):
    parser_classes = [JSONParser, FormParser, MultiPartParser]
    permission_classes = [permissions.AllowAny]
    serializer_class = GoogleUrlSerializer

    @extend_schema(tags=["social authentication"])
    def get(self, request, *args, **kwargs):
        """Generate Google OAuth URL for frontend"""
        base_url = "https://accounts.google.com/o/oauth2/v2/auth"
        state = generate_state(request)

        params = {
            "client_id": settings.SOCIAL_AUTH_GOOGLE_OAUTH2_KEY,
            "redirect_uri": f"{settings.BACKEND_URL}/api/oauth/complete/google-oauth2/",
            "state": state,
            "scope": "openid email profile",
            "response_type": "code",
            "access_type": "offline",
            "prompt": "consent",
        }

        auth_url = f"{base_url}?{urlencode(params)}"
        return Response({"auth_url": auth_url})


class GoogleOAuthCompleteView(generics.GenericAPIView):
    parser_classes = [JSONParser, FormParser, MultiPartParser]

    permission_classes = [permissions.AllowAny]
    serializer_class = GoogleAuthCompleteSerializer

    def get(self, request):
        token_data = request.session.get("jwt_data")

        if not token_data:
            return Response(
                {"error": "Authentication failed or no token found."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        request.session.pop("jwt_data", None)

        return Response(
            token_data["access_token"],
            message="User Successfully authenticated",
            status=status.HTTP_200_OK,
        )


class SocialTokenObtainView(generics.GenericAPIView):
    parser_classes = [JSONParser, FormParser, MultiPartParser]
    permission_classes = [permissions.AllowAny]
    token_class = RefreshToken

    @classmethod
    def get_token(cls, user) -> Token:
        return cls.token_class.for_user(user)

    @extend_schema(tags=["social authentication"])
    def get(self, request, *args, **kwargs):
        try:
            user = request.user
        except Exception as e:
            return Response(
                {"error": str(e)}, status=status.HTTP_400_BAD_REQUEST
            )
        refresh = (
            self.get_token(user) if user.extra_data else None
        )  # Checks if user is instance of UserSocialAuth
        data = {
            "refresh_token": str(refresh),
            "access_token": str(refresh.access_token),
        }

        response = Response()
        if hasattr(request, "session") and data["access_token"]:
            request.session["access_token"] = data["access_token"]
            request.session["refresh_token"] = data["refresh_token"]
            request.session["user"] = user.pk

        del data["refresh"]
        response.data = data
        response.status_code = status.HTTP_200_OK
        return response


class SignUpview(generics.CreateAPIView):
    permission_classes = [permissions.AllowAny]
    parser_classes = [JSONParser, FormParser, MultiPartParser]
    serializer_class = UserSignUpSerializer
    queryset = User.objects.none()

    @extend_schema(tags=["authentication"])
    def post(self, request, *args, **kwargs):
        try:
            with transaction.atomic():
                logger.info("Initializing signup request")
                serializer = UserSignUpSerializer(data=request.data)
                serializer.is_valid(raise_exception=True)
                user = serializer.save()
                transaction.on_commit(
                    lambda: send_email(
                        request, user, mail_type="email_verification", kwargs={}
                    )
                )
                logger.debug("Send mail celery task would be executed after view block")
                return Response(
                    {
                        "message": "User Created, mail task has been assigned. User can try again after 5 minutes",
                    },
                    status=status.HTTP_201_CREATED,
                )
        except Exception as e:
            return Response(
                {"message": "An error occurred", "error": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )


class UserPasswordResetRequestView(views.APIView):
    permission_classes = [permissions.AllowAny]
    parser_classes = [JSONParser, FormParser, MultiPartParser]
    serializer_class = UserPasswordResetSerializer

    def _get_user(self, request, email):

        if request.user.is_authenticated:
            return request.user

        if email:
            try:
                return User.objects.get(email=email)
            except User.DoesNotExist:
                logger.warning(f"User with email {email} does not exist.")
                return None
        return None

    @extend_schema(tags=["authentication"])
    def post(self, request: Request, *args, **kwargs):
        try:
            serializer = self.serializer_class(data=request.data)
            serializer.is_valid(raise_exception=True)

            user = self._get_user(request, serializer.validated_data.get("email"))
            link = None

            if user:
                link = send_email(
                    request=request, user=user, mail_type="password_reset", kwargs={}
                )
            response_payload = {
                "message": "If an account exists for this email, you’ll receive a password reset link",
            }
            if link:
                response_payload["link"] = link
            return Response(
                response_payload,
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            logger.error(f"Error in post method: {str(e)}")
            return Response(data=str(e))


class UserPasswordResetConfirmView(generics.GenericAPIView):
    serializer_class = UserNewPasswordResetSerializer
    parser_classes = [JSONParser, FormParser, MultiPartParser]
    permission_classes = [permissions.AllowAny]
    queryset = User.objects.none()

    @extend_schema(tags=["authentication"])
    def post(self, request, token, safe):

        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        token_serializer = TokenVerificationSerializer(
            data={"token": token, "safe": safe}
        )
        token_serializer.is_valid(raise_exception=True)
        token_data = token_serializer.validated_data

        logger.debug(
            f"This is the serialized data: {data}, query_params:{request.query_params}"
        )
        value = verify_token(token=token_data["token"], safe=token_data["safe"])
        if isinstance(value, Response):
            return Response(value.data, status=value.status_code)
        if isinstance(value, User):
            serializer.instance = value
            serializer.save()
            send_email(request, user=value, mail_type="password_reset_success")
            return Response(
                {
                    "message": f"{value.username}, password successfully updated.",
                },
                status=status.HTTP_200_OK,
            )
        return Response(
            {"error": "Invalid link or link expired"},
            status=status.HTTP_400_BAD_REQUEST,
        )


class DeleteView(generics.DestroyAPIView):
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [JSONParser, FormParser, MultiPartParser]
    serializer_class = TokenVerificationSerializer

    def get_queryset(self):
        return self.request.user

    def get_object(self):
        if hasattr(self.request, "session"):
            user_id = self.request.session.get("_auth_user_id")
            return User.objects.get(id=user_id)
        return None

    @extend_schema(tags=["authentication"])
    def get(self, request):
        try:
            user = request.user
            link = send_email(request=request, user=user, mail_type="delete_account")
            return Response(
                {"message": "E-mail to confirm account deletion sending", "link": link},
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            return Response(
                {"message": "An unknown error occurred", "error": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )

    @extend_schema(
        tags=["authentication"],
        parameters=[
            OpenApiParameter("token", str, required=False),
            OpenApiParameter("safe", str, required=False),
        ],
    )
    def delete(self, request, *args, **kwargs):
        query_params = request.query_params
        request_data = {
            "safe": query_params.get("safe"),
            "token": query_params.get("token"),
        }
        serializer = self.serializer_class(data=request_data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        value = verify_token(**data)
        if isinstance(value, User) and hasattr(request, "session"):
            response = super().delete(self, request)
            return Response(
                data=response.data,
                message="User account successfully deleted",
                status=response.status_code,
            )
        return Response(
            {"error": "No session found"}, status=status.HTTP_400_BAD_REQUEST
        )


class LogoutView(generics.GenericAPIView):
    permission_classes = [permissions.AllowAny]
    parser_classes = [JSONParser, FormParser, MultiPartParser]
    serializer_class = UserLogoutSerializer

    def get_queryset(self):
        request = getattr(self, "request", None)
        if request and hasattr(request, "user"):
            return User.objects.filter(id=request.user.id)
        return User.objects.none()

    @extend_schema(tags=["authentication"])
    def post(self, request):
        try:
            if hasattr(request, "session"):
                user = request.user
                response = Response(
                    {"message": f"{user.username} successfully logged out"},
                    status=status.HTTP_205_RESET_CONTENT,
                )
                logout(request)
                if isinstance(user, User):
                    return response
                else:
                    raise TypeError("User is not authenticated")
        except Exception as e:
            return Response(
                {"error": str(e), "message": "An error occured while logging out"},
                status=status.HTTP_401_UNAUTHORIZED,
            )


class ReactivateDeactivateUserAccount(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [JSONParser, FormParser, MultiPartParser]
    serializer_class = ReactivateDeactivateUserSerializer

    def get_object(self):
        return self.request.user

    @extend_schema(
        tags=["authentication"],
        responses={200: "Success", 400: "Bad Request"},
        description="Choose 'deactivate' to deactivate user account or 'reactivate' to reactivate it",
    )
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid()
        deactivate_account = bool(serializer.data["action"] == "deactivate")
        user = self.get_object()
        user.is_active = False if deactivate_account else True
        user.save(update_fields=["is_active"])

        return Response(
            {
                "message": f"User account {'deactivated' if deactivate_account else 'reactivated'}"
            },
            status=status.HTTP_200_OK,
        )


@extend_schema_view(
    get=extend_schema(
        tags=["authentication"],
        description="Retrieve the details of the currently logged in user.",
    )
)
class UserDetailView(generics.RetrieveAPIView):
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [JSONParser, FormParser, MultiPartParser]
    serializer_class = UserDetailSerializer

    def get_object(self):
        id = self.kwargs.get("pk")
        if id:
            queryset = get_user_model().objects.get(id=id)
        else:
            queryset = self.request.user
        return queryset
