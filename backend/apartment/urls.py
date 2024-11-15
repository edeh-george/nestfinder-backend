from django.urls import path, re_path
from . views import *

app_name = 'apartment'

urlpatterns = [
    path('apartment-list/', ApartmentListGenerics.as_view(), name='apartment'),
    path('apartment/<uuid:pk>/', ApartmentDetailView.as_view(), name='apartment-detail'),
    re_path(r'^api/v1/apartment/(?P<pk>(\d+|[0-9a-fA-F-]{36}))/$',
            ApartmentManageView.as_view(),
            name='apartment-manage'),
]
