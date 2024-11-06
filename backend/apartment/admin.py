from django.contrib import admin
from . models import Apartment

# Register your models here.
@admin.register(Apartment)
class UserAdmin(admin.ModelAdmin):
    list_display = ['name', 'apartment_type', 'description', 'price', 'location', 'is_leased']