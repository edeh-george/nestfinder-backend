from django.urls import path
from .views import *


urlpatterns = [
    path("mail/user-auth/", sendAuthMail.as_view(), name='auth-mail'),
    path("mail/verify-token/", verifyAuthToken.as_view()),
    path("mail/send-mail/", LandlordContactMail.as_view(), name='send-landlord-mail'),
]
