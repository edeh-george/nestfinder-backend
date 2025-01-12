from rest_framework import filters
from apartment.models import Apartment

LOCATION = Apartment.LOCATION
LOCATION_MAP = {value.lower(): key for key, value in dict(LOCATION).items()}


class LocationFilterBackend(filters.BaseFilterBackend):
    def filter_queryset(self, request, queryset, view):
        location_param = request.query_params.get('location', '').lower()
        location_abbrev = LOCATION_MAP.get(location_param)
        if location_abbrev:
            queryset = queryset.filter(location__icontains = location_abbrev)
        return queryset
 
 
APARTMENT = Apartment.APARTMENT_LIST
APARTMENT_MAP = {value.lower(): key for key, value in dict(APARTMENT).items()}

class ApartmentFilterBackend(filters.BaseFilterBackend):
    def filter_queryset(self, request, queryset, view):
        apartment_param = request.query_params.get('apartment_type', '').lower()
        apartment_type = APARTMENT_MAP.get(apartment_param)
        if apartment_type:
            print(apartment_type)
            queryset = queryset.filter(apartment_type=apartment_type)
        return queryset
        