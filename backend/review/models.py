from django.db import models
from django.contrib.auth import get_user_model
from apartment.models import Apartment

User = get_user_model()

class Review(models.Model):
    comment = models.TextField(blank=True, null=True)
    rating = models.PositiveSmallIntegerField(blank=True, null=True)
    user = models.ForeignKey(User,
                             on_delete=models.CASCADE,
                             related_name='user_review')
        
    apartment = models.ForeignKey(Apartment,
                             on_delete=models.CASCADE,
                             related_name='apartment')
    is_active = models.BooleanField(default=True)
    likes = models.PositiveBigIntegerField(default='', null=True)
    dislikes = models.PositiveBigIntegerField(default='', null=True)
    created = models.DateTimeField(auto_now_add=True)