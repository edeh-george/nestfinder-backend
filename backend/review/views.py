from django_filters.rest_framework.backends import DjangoFilterBackend
from rest_framework import generics
from rest_framework.filters import SearchFilter
from rest_framework.permissions import AllowAny
from rest_framework_json_api.filters import OrderingFilter
from userauth.authentication import CustomAuthentication
from userauth.permissions import canModifyPermission

from .models import Review
from .serializers import ReviewSerializer


class ReviewListing(generics.ListAPIView):
    permission_classes = [AllowAny]
    authentication_classes = [CustomAuthentication]
    serializer_class = ReviewSerializer
    filter_backends = [SearchFilter, DjangoFilterBackend, OrderingFilter]
    search_fields = ["comment"]
    ordering_fields = "__all__"
    ordering = ["-created"]

    def get_queryset(self):
        apartment_id = self.kwargs.get("apartmentId")
        queryset = Review.objects.filter(apartment__id=apartment_id)
        return queryset


class ReviewManagerView(
    generics.CreateAPIView, generics.UpdateAPIView, generics.DestroyAPIView
):

    permission_classes = [canModifyPermission]
    authentication_classes = [CustomAuthentication]
    serializer_class = ReviewSerializer
