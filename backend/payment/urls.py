from django.urls import path
from . views import *


urlpatterns = [
    path('payment/start/', StartPaymentView.as_view(), name='start-payment')     
]
