from django.contrib import admin
from . models import Apartment, ApartmentImage

# Register your models here.
@admin.register(Apartment)
class ApartmentAdmin(admin.ModelAdmin):
    list_display = ['name', 'apartment_type', 'description', 'price', 'location', 'is_leased']
    list_filter = ['name', 'apartment_type', 'location', 'is_leased']
    
@admin.register(ApartmentImage)
class ApartmentImagesAdmin(admin.ModelAdmin):
    list_display = ['id', 'apartment']