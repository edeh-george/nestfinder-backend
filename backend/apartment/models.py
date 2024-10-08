from django.db import models


class Apartment(models.Model):
    LOCATION = [
        ('ODI', 'Odim'),
        ('ODE', 'Odenigwe'),
        ('BF', 'Behind Flat'),
        ('GH', 'Green House'),
        ('HT', 'Hilltop'),
        ('SQ', 'Staff Quarters')
    ]
    name = models.CharField(max_length=255)
    apartment_type = models.CharField(max_length=50, 
                                      choices= [('one_room', 'One room'), ('self_con', 'Self con'),
                                                ('room_and_parlour', 'A room and parlour')],
                                                default='one_room')
    description = models.TextField()
    image = models.FileField(upload_to='files/')
    price = models.PositiveIntegerField()
    location = models.CharField(max_length=255,
                                choices=LOCATION, default='HT')
    is_leased = models.BooleanField(default=False)
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)