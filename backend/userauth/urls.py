from django.urls import path 
from rest_framework_simplejwt.views import TokenRefreshView
from . views import *

urlpatterns = [
    path('token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('signup/', SignUpview.as_view(), name='signup'),
    path('verify/', VerifyEmailView.as_view(), name='verify'),
    path('password/reset/', UserPasswordResetView.as_view(), name='reset'),
    path('logout/', LogoutView.as_view(), name='logout'),
]