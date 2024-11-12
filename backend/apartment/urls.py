from django.urls import path
from . views import *

app_name = 'apartment'

urlpatterns = [
    path('apartment/', ApartmentListGenerics.as_view(), name='apartment'),
    path('apartment/<uuid:pk>/', ApartmentDetailView.as_view(), name='apartment-detail'),
]
