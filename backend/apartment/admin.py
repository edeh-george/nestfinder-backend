from django.contrib import admin

from .models import Apartment, ApartmentImage


# Register your models here.
@admin.register(Apartment)
class ApartmentAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "apartment_type",
        "description",
        "price",
        "location",
        "is_leased",
        "apartment_list",
    ]
    list_filter = ["name", "apartment_type", "location", "is_leased"]

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related("apartments")

    def apartment_list(self, obj):
        return ", ".join(o.name for o in obj.apartments.all())


@admin.register(ApartmentImage)
class ApartmentImagesAdmin(admin.ModelAdmin):
    list_display = ["id", "apartment"]
