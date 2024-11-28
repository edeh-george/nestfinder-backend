from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import RegexValidator, MinValueValidator


User = get_user_model()


phone_regex = RegexValidator(
        regex=r'^\+?234?\d{9,15}$',
        message="Phone number must be entered in the format: \
            \'+234xxxxxxx\'. Cannot be more that 9 digits and a maximum of 15 digits is allowed."
        )

class Profile(models.Model):

    
    user = models.OneToOneField(User, on_delete=models.CASCADE,
                                related_name='user_profile')
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True)
    phone_number = models.CharField(max_length=17, validators=[phone_regex])
    date_of_birth = models.DateField()
    preferred_location = models.CharField(max_length=255)
    budget_range_min = models.DecimalField(max_digits=10, decimal_places=2)
    budget_range_max = models.DecimalField(max_digits=10, decimal_places=2)
    lease_duration = models.CharField(max_length=50, choices=[('6_months', '6 Months'), ('1_year', '1 Year'), ('other', 'Other')])
    year_of_study = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    field_of_study = models.CharField(max_length=255, blank=True)

