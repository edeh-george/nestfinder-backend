from django.db import models


class Apartment(models.Model):
    apartment_type = models.CharField(max_length=50, 
                                      choices= [('one_room', 'One room'), ('self_con', 'Self con'),
                                                ('room_and_parlour', 'A room and parlour')],
                                                default='one_room')
    description = models.TextField()
    image = models.FileField(upload_to=...)
    price = models.PositiveIntegerField()
    location = models.CharField(max_length=255, blank=False, null=False)