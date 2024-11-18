from django.urls import path
from . views import *


urlpatterns = [
    path('reviews/<uuid:apartmentId>/', ReviewListing.as_view(), name='review-list'),
]
