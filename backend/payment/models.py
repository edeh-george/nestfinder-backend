from django.db import models
import secrets
from django.conf import settings
from .paystack import Paystack

User = settings.AUTH_USER_MODEL

class Payment(models.Model):
    # STATUS_CHOICES = (
    #     ('pending', 'Pending'),
    #     ('success', 'Success'),
    #     ('failed', 'Failed')
    # )
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    amount = models.FloatField(blank=True, null=True)
    ref = models.CharField(max_length=250)
    email = models.CharField(max_length=250)
    verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_add_now=True)


    def __str__(self):
        return f"{self.user} - {self.amount}"
    
    def save(self, *args, **kwargs):
        while not self.ref:
            ref = secrets.token_urlsafe(50)
            objects_with_similar_ref = Payment.objects.filter(ref=ref)
            if not objects_with_similar_ref:
                self.ref = ref
        super().save(*args, **kwargs)

    def amount_value(self):
        return int(self.amount) * 100
    
    def verify_payment(self):
        paystack = Paystack()
        status, result = paystack.verify_payment(self.ref, self.amount)
        if status:
            if result['amount'] /100 == self.amount:
                self.verified = True
                self.save()
        if self.verified:
            return True
        return False