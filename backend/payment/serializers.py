from rest_framework import serializers
from .models import Payment


class PaymentInitSerializer(serializers.Serializer):
    email = serializers.CharField(required=True)
    amount = serializers.DecimalField(max_digits=10, decimal_places=2)

class PaymentSerializer(serializers.ModelSerializer):

    class Meta:
        model = Payment
        fields = '__all__'
        
class PaymentVerifySerializer(serializers.Serializer):
    reference = serializers.CharField(required=True)