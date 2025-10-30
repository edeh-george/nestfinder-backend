import os

import requests
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from rest_framework import generics, status
from rest_framework.decorators import (
    api_view,
    authentication_classes,
    permission_classes,
)
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from userauth.authentication import CustomAuthentication

from .models import Payment
from .serializers import (
    PaymentInitSerializer,
    PaymentSerializer,
    PaymentVerifySerializer,
)

PAYSTACK_SECRET_KEY = os.getenv("PAYSTACK_SECRET_KEY")
FRONTEND_URL = os.getenv("FRONTEND_URL")


class InitiatePayment(generics.GenericAPIView):
    authentication_classes = [CustomAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = PaymentInitSerializer

    def post(self, request, *args, **kwargs):
        user = request.user
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data.get("email")
        amount = serializer.validated_data.get("amount")

        if not email or not amount:
            return Response(
                {"error": "Email and amount are required fields."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        payment = Payment.objects.create(user=user, email=email, amount=amount)

        url = "https://api.paystack.co/transaction/initialize"
        headers = {"Authorization": f"Bearer {PAYSTACK_SECRET_KEY}"}
        payload = {
            "email": email,
            "amount": int(amount) * 100,  # Convert to kobo
            "callback_url": f"http://{FRONTEND_URL}/payment/verify/",
            "reference": payment.ref,
        }
        response = requests.post(url, headers=headers, json=payload)
        if response.status_code != 200:
            return Response(
                {"error": "Failed to initialize payment.", "details": response.json()},
                status=response.status_code,
            )

        return Response(response.json(), status=status.HTTP_200_OK)


class GetPaymentView(generics.RetrieveAPIView):
    authentication_classes = [CustomAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = PaymentSerializer

    def get_object(self, *args, **kwargs):
        payment = get_object_or_404(Payment, ref=self.kwargs["reference"])
        return payment


class VerifyPayment(generics.GenericAPIView):
    authentication_classes = [CustomAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = PaymentVerifySerializer

    def post(self, request, *args, **kwargs):
        try:
            serializer = self.serializer_class(data=request.data)
            serializer.is_valid(raise_exception=True)
            reference = serializer.validated_data.get("reference")
            payment = Payment.objects.get(ref=reference)
            payment.verify_payment()
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response({"status": payment.verified}, status=status.HTTP_200_OK)


@api_view(["GET"])
@permission_classes([IsAdminUser])
@authentication_classes([CustomAuthentication])
@csrf_exempt
def list_transactions(request):
    url = "https://api.paystack.co/transaction"
    headers = {"Authorization": f"Bearer {PAYSTACK_SECRET_KEY}"}
    response = requests.get(url, headers=headers)
    return Response(response.json(), status=status.HTTP_200_OK)
