from django.urls import path

from .views import *

urlpatterns = [
    path("reviews/<int:apartmentId>/", ReviewListing.as_view(), name="review-list"),
]
