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
from userauth.permissions import canModifyPermission
from rest_framework.response import Response
from rest_framework import status
from rest_framework.parsers import MultiPartParser, JSONParser
import os 
import json


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

        image_queryset = apartment.images.all()
        related_apartment_queryset = apartment.objects.filter(
            is_leased=False,
            location=apartment.location
        ).exclude(id=apartment.id)
        # apartment.apartments.add(*related_apartment_queryset)
        apartment = Apartment.objects.prefetch_related(
            Prefetch('images', queryset=image_queryset, to_attr='image_list'),
            Prefetch('apartments', queryset=related_apartment_queryset, to_attr='related_apartment')
        ).get(id=apartment.id)

        return apartment

    
    
    
class ApartmentManageView(generics.CreateAPIView,
                                      generics.UpdateAPIView,
                                      generics.DestroyAPIView):
    
    permission_classes = [canModifyPermission]
    serializer_class = ApartmentSerializer
    
    
    
import random
from django.core.files import File
class BulkCreateApartmentView(generics.GenericAPIView):
    parser_classes = [MultiPartParser, JSONParser]

    def get(self, request, *args, **kwargs):
        file_path = os.path.abspath('../apartments_data_new.json')
        
        if not os.path.exists(file_path):
            return Response({"error": "JSON file not found"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            with open(file_path, 'r') as json_file:
                apartment_data = json.load(json_file)

            image_paths = [
                '/home/george/Downloads/image1.jpg',
                '/home/george/Downloads/image2.jpg',
                '/home/george/Downloads/image3.jpg',
                '/home/george/Downloads/image4.jpg',
                '/home/george/Downloads/image5.jpg'
            ]

            apartments = []
            for apartment in apartment_data:
                apartment_instance = Apartment(
                    name=apartment['name'],
                    apartment_type=apartment['apartment_type'],
                    description=apartment['description'],
                    price=apartment['price'],
                    location=apartment['location'],
                    is_leased=apartment['is_leased'],
                    uploaded_by_id=apartment['uploaded_by']
                )
                apartments.append(apartment_instance)

            Apartment.objects.bulk_create(apartments)

            created_apartments = Apartment.objects.filter(id__in=[a.id for a in apartments])

            for apartment in created_apartments:
                random_image_path = random.choice(image_paths)
                with open(random_image_path, 'rb') as img_file:
                    apartment.image.save('main.jpg', File(img_file), save=False)

            Apartment.objects.bulk_update(created_apartments, ['image'])

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response({"message": f"{len(apartments)} Apartments created successfully!"}, status=status.HTTP_201_CREATED)