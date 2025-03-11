from django.urls import path, re_path
from . views import *


urlpatterns = [
    path('payment/initiate/', InitiatePayment.as_view(), name='initiate-payment'),
    re_path(r'payment/verify/', VerifyPayment.as_view(), name='verify-payment'),
]
