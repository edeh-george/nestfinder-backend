from django.db import models
from userauth.models import UserModel
from taggit.managers import TaggableManager
import os, uuid


def user_directory_path(instance, filename):
    user_id = instance.uploaded_by.id if isinstance(instance, Apartment) else instance.apartment.uploaded_by.id
    apartment_id = instance.id if isinstance(instance, Apartment) else instance.apartment.id
    return os.path.join(f'user_{user_id}', f'apartment_image_{apartment_id}', filename)

class UUidModelAbstract(models.Model):
    # id = models.UUIDField(primary_key=True, auto_created=True,
    #                       default=uuid.uuid4, unique=True)
    id = models.BigAutoField(primary_key=True)
    
    class Meta:
        abstract = True


class Apartment(UUidModelAbstract, models.Model):

    LOCATION = [
        ('ODI', 'Odim'),
        ('ODE', 'Odenigwe'),
        ('BF', 'Behind Flat'),
        ('GH', 'Green House'),
        ('HT', 'Hilltop'),
        ('SQ', 'Staff Quarters')
    ]
    
    APARTMENT_LIST = [
            ('one_room', 'One room'),
            ('self_con', 'Self con'),
            ('room_and_parlour', 'A room and parlour')
        ]
    
    uploaded_by = models.ForeignKey(
        UserModel,
        on_delete=models.CASCADE,
        related_name='apartments'
    )
    
    name = models.CharField(max_length=255, null=True, blank=True)
    apartment_type = models.CharField(
        max_length=50, 
        choices= APARTMENT_LIST,
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
    image = models.ImageField(upload_to=user_directory_path, blank=True, null=True)
    apartments = TaggableManager(verbose_name="Related Apartments")
    
    def __str__(self):
        return str(self.id)

class ApartmentImage(UUidModelAbstract, models.Model):
    apartment = models.ForeignKey(
        Apartment,
        on_delete=models.CASCADE,
        related_name='images'
    )
    images = models.ImageField(upload_to=user_directory_path)
    
    
    def __str__(self):
        return f"image of {self.apartment.name}"