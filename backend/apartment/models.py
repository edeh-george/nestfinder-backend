from django.db import models
from django.utils import timezone
from userauth.models import UserModel
import os
from django.db.models import Count


def user_directory_path(instance, filename):
    user_id = instance.uploaded_by.id if isinstance(instance, Apartment) else instance.apartment.uploaded_by.id
    apartment_id = instance.id if isinstance(instance, Apartment) else instance.apartment.id
    if not apartment_id:
        instance.save()
    return os.path.join(f'user_{user_id}', f'apartment_{apartment_id}', filename)

class Apartment(models.Model):
    LOCATION = [
        ('ODI', 'Odim'),
        ('ODE', 'Odenigwe'),
        ('BF', 'Behind Flat'),
        ('GH', 'Green House'),
        ('HT', 'Hilltop'),
        ('SQ', 'Staff Quarters')
    ]
    
    uploaded_by = models.ForeignKey(
        UserModel,
        on_delete=models.CASCADE,
        related_name='apartments'
    )
    
    name = models.CharField(max_length=255, null=True, blank=True)
    apartment_type = models.CharField(
        max_length=50, 
        choices=[
            ('one_room', 'One room'),
            ('self_con', 'Self con'),
            ('room_and_parlour', 'A room and parlour')
        ],
        default='one_room'
    )
    description = models.TextField()
    price = models.PositiveIntegerField()
    location = models.CharField(
        max_length=255,
        choices=LOCATION, default='HT'
    )
    is_leased = models.BooleanField(default=False)
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)
    # This represents the main image for the house, and saves time by reducing overhead in querying all the images
    image = models.ImageField(upload_to=user_directory_path, blank=True, null=True)

class ApartmentImage(models.Model):
    apartment = models.ForeignKey(
        Apartment,
        on_delete=models.CASCADE,
        related_name='images'
    )
    images = models.ImageField(upload_to=user_directory_path)
    
    def __str__(self):
        return f"image of {self.apartment.name}"