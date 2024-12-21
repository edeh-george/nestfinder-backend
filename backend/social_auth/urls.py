from django.urls import path
from .views import *


app_name = 'social_auth'

urlpatterns = [
    path('', display_user_details),
]
