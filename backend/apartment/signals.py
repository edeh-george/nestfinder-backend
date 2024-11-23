from django.db.models.signals import post_save
from django.dispatch import receiver
from . models import Apartment


@receiver(post_save, sender=Apartment)
def create_related_apartments(sender, instance, *args, **kwargs):
    filtered_apartments = Apartment.objects.filter(
        location=instance.location).exclude(id=instance.id)
    
    apartment_tag = [str(_.id) for _ in filtered_apartments]
    
    instance.apartments.set(*apartment_tag)
    print(apartment_tag)