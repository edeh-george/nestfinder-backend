from .serializers import (ApartmentSerializer,
                          ApartmentDetailSerializer)
from django_filters.rest_framework.backends import DjangoFilterBackend
from rest_framework_json_api.filters import OrderingFilter
from rest_framework.filters import SearchFilter
from . filters import LocationFilterBackend, ApartmentFilterBackend
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework import generics
from .models import Apartment, ApartmentImage
from userauth.authentication import CustomAuthentication
import django_filters
from  django.shortcuts import get_object_or_404
from django.db.models import Prefetch
from ..userauth.permissions import canModifyPermission


# Create your views here.
class ApartmentFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(field_name='name', lookup_expr='icontains')
    start_price = django_filters.NumberFilter(field_name='price', lookup_expr='gte')
    end_price = django_filters.NumberFilter(field_name='price', lookup_expr='lte')
    is_leased = django_filters.BooleanFilter(field_name='is_leased')
    date_from = django_filters.DateFilter(field_name='created', lookup_expr='gte')
    date_to = django_filters.DateFilter(field_name='created', lookup_expr='lte')
    apartment_type = django_filters.CharFilter(field_name='apartment_type', lookup_expr='icontains')

    class Meta:
        model = Apartment
        fields = [
            'name','date_from', 'date_to', 'start_price', 'end_price',
            'is_leased'
        ]


class ApartmentListGenerics(generics.ListAPIView):
    permission_classes = [AllowAny]
    # authentication_classes = [CustomAuthentication]
    filter_backends = [DjangoFilterBackend, OrderingFilter, SearchFilter,
                       LocationFilterBackend, ApartmentFilterBackend]
    filterset_class = ApartmentFilter
    search_fields = ['name']
    ordering_fields = '__all__'
    ordering = ['-created']
    serializer_class = ApartmentSerializer
    
    def get_queryset(self):
        queryset = Apartment.objects.all()
        if not self.request.query_params.get('ordering'):
            #This is computational expensive for large datasets consider caching
            queryset = Apartment.objects.all().order_by('?')
            
        return queryset
    
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)
             

class ApartmentDetailView(generics.RetrieveAPIView):
    serializer_class = ApartmentDetailSerializer
    permission_classes = [AllowAny]
    
    def get_object(self, *args, **kwargs):
        apartment = get_object_or_404(Apartment, id=self.kwargs['pk'])
        apartment = Apartment.objects.prefetch_related(
            Prefetch('images', queryset=ApartmentImage.objects.all(), to_attr='image_list')
        ).get(id=apartment.id)
        return apartment

    
    
    
class ApartmentManageView(generics.CreateAPIView,
                                      generics.UpdateAPIView,
                                      generics.DestroyAPIView):
    
    permission_classes = [canModifyPermission]
    serializer_class = ApartmentSerializer
