from django.urls import path, re_path

from . import views as auth_views

app_name = "authentication"


urlpatterns = [
    path(
        "token/",
        auth_views.CustomTokenObtainPairView.as_view(),
        name="token_obtain_pair",
    ),
    path(
        "token/refresh/",
        auth_views.CustomTokenRefreshView.as_view(),
        name="token_refresh",
    ),
    path("signup/", auth_views.SignUpview.as_view(), name="signup"),
    re_path(
        r"^verify/(?P<token>[^/]+)/(?P<safe>[^/]+)$",
        auth_views.VerifyEmailView.as_view(),
        name="verify",
    ),
    path(
        "password/reset/",
        auth_views.UserPasswordResetRequestView.as_view(),
        name="password_reset",
    ),
    re_path(
        r"^password/reset/new/(?P<token>[\w=-]+)/(?P<safe>[\w=-]+)$",
        auth_views.UserPasswordResetConfirmView.as_view(),
        name="verify_password_reset_and_update",
    ),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    re_path(
        # r"^user/(?P<id>[\w=-]+)?$",
        r"user/",
        auth_views.UserDetailView.as_view(),
        name="user-detail",
    ),
    path(
        "delete/",
        auth_views.DeleteView.as_view(),
        name="delete",
    ),
    path(
        "google-login/", auth_views.GoogleLoginURLAPIView.as_view(), name="google_login"
    ),
    path(
        "complete/google/",
        auth_views.GoogleOAuthCompleteView.as_view(),
        name="google_login_complete",
    ),
    path(
        "deactivate-reactive-user/",
        auth_views.ReactivateDeactivateUserAccount.as_view(),
        name="reactivate_deactivate_user_account",
    ),
]
