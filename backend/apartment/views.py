from .serializers import ApartmentSerializer
from django_filters.rest_framework.backends import DjangoFilterBackend
from rest_framework_json_api.filters import OrderingFilter
from rest_framework.filters import SearchFilter
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework import generics
from .models import Apartment
from ..userauth.authentication import CustomAuthentication
import django_filters


# Create your views here.
class ApartmentFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(field_name='name', lookup_expr='icontains')
    start_price = django_filters.NumberFilter(field_name='price', lookup_expr='gte')
    end_price = django_filters.NumberFilter(field_name='price', lookup_expr='lte')
    is_leased = django_filters.BooleanFilter(field_name='is_leased')
    date_from = django_filters.DateFilter(field_name='created', lookup_expr='gte')
    date_to = django_filters.DateFilter(field_name='created', lookup_expr='lte')
    #remember to add filter for location

    class Meta:
        model = Apartment
        fields = [
            'name','date_from', 'date_to', 'start_price', 'end_price',
            'is_leased'
        ]

class ApartmentListGenerics(generics.ListAPIView):
    permission_classes = [AllowAny]
    authentication_classes = [CustomAuthentication]
    queryset = Apartment.objects.all()
    filter_backends = [DjangoFilterBackend, OrderingFilter, SearchFilter]
    filterset_class = ApartmentFilter
    search_fields = ['name', 'location']
    ordering_fields = '__all__'
    ordering = ['-created']
    serializer_class = ApartmentSerializer

