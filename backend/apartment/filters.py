from rest_framework import filters

LOCATION_MAP = {
    'odim': 'ODI',
    'odenigwe': 'ODE',
    'behind flat': 'BF',
    'green house': 'GH',
    'hilltop': 'HT',
    'staff quarters': 'SQ',
}

class LocationFilterBackend(filters.BaseFilterBackend):
    def filter_queryset(self, request, queryset, view):
        location_param = request.query_params.get('location', '').lower()
        location_abbrev = LOCATION_MAP.get(location_param)
        if location_abbrev:
            queryset = queryset.filter(location=location_abbrev)
        return queryset
