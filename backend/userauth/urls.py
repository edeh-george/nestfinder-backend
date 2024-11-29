from django.urls import path, re_path
from rest_framework_simplejwt.views import TokenRefreshView
from . views import *

app_name = "userauth"


urlpatterns = [
    path('token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('signup/', SignUpview.as_view(), name='signup'),
    re_path(r'^verify/(?P<token>[\w=-]+)/(?P<safe>[\w=-]+)$', VerifyEmailView.as_view(), name='verify'),
    path('password/reset/', UserPasswordResetRequestView.as_view(), name='reset-password'),
    re_path(r'^password/reset/confirm/(?P<token>[\w=-]+)/(?P<safe>[\w=-]+)$', VerifyPasswordResetView.as_view(), name='verify-password-reset'),
    re_path(r'^password/reset/new/(?P<safe>[\w=-]+)$', UserPasswordResetConfirmView.as_view(), name='new-password'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('user/<int:pk>', UserDetailView.as_view(), name='user-detail'),
]
