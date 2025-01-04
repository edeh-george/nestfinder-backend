from django.urls import path
from .views import *


app_name = 'social_auth'

urlpatterns = [
    path('', TokenObtainView.as_view()),
]
