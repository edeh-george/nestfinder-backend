from django.db import models
from django.contrib.auth import get_user_model
from apartment.models import Apartment

User = get_user_model()

class Review(models.Model):
    comment = models.TextField(blank=True, null=True)
    rating = models.PositiveSmallIntegerField(blank=True, null=True)
    user = models.ForeignKey(User,
                             on_delete=models.CASCADE,
                             related_name='user')
        
    apartment = models.ForeignKey(Apartment,
                             on_delete=models.CASCADE,
                             related_name='apartment')
    is_active = models.BooleanField(default=True)
    like = models.PositiveIntegerField(default=0)
    dislike  = models.PositiveIntegerField(default=0)
    created = models.DateTimeField(auto_now_add=True)