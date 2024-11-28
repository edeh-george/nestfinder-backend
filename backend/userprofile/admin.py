from django.contrib import admin
from . models import Profile


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ['id', 'phone_number', 'year_of_study', 'field_of_study']
    