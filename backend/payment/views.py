from rest_framework import status
from rest_framework import generics
from django.shortcuts import get_object_or_404
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny
from userauth.authentication import CustomAuthentication
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from .models import Payment
from . serializers import PaymentSerializer, PaymentInitSerializer
import requests
import os


from django.views.decorators.csrf import csrf_exempt

PAYSTACK_SECRET_KEY = os.getenv("PAYSTACK_SECRET_KEY")
FRONTEND_URL = os.getenv("FRONTEND_URL")

class InitiatePayment(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [CustomAuthentication]
    serializer_class = PaymentInitSerializer

    # @csrf_exempt
    def post(self, request, *args, **kwargs):
        try:
            user = request.user
            data = request.data

            email = data.get("email")
            amount = data.get("amount")

            if not email or not amount:
                return Response(
                    {"error": "Email and amount are required fields."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            if user.email != email:
                return Response(
                    {"error": "The email provided does not match the logged-in user."},
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

            return Response({"data": response.json()}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class GetPaymentView(generics.RetrieveAPIView):
    authentication_classes = [CustomAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = PaymentSerializer

    def get_object(self, *args, **kwargs):
        payment = get_object_or_404(Payment, ref=self.kwargs['reference'])
        return payment

class VerifyPayment(generics.GenericAPIView):
    authentication_classes = CustomAuthentication
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        try:
            trxref = request.query_params.get('trxref')
            reference = request.query_params.get('reference')
            payment = Payment.objects.get(ref=reference)
            payment.verify_payment()
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response({"status":payment.verified}, status=status.HTTP_200_OK)
    

@api_view(["GET"])
@permission_classes([IsAdminUser])
@authentication_classes([CustomAuthentication])
def list_transactions(request):
    url = "https://api.paystack.co/transaction"
    headers = {"Authorization": f"Bearer {PAYSTACK_SECRET_KEY}"}
    response = requests.get(url, headers=headers)
    return Response(response.json(), status=status.HTTP_200_OK)


from rest_framework.decorators import api_view, permission_classes, authentication_classes

@api_view(['POST'])
@permission_classes([IsAuthenticated])
@authentication_classes([CustomAuthentication])
def initiate_payment(request):
    try:
            user = request.user
            data = request.data

            email = data.get("email")
            amount = data.get("amount")

            if not email or not amount:
                return Response(
                    {"error": "Email and amount are required fields."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            if user.email != email:
                return Response(
                    {"error": "The email provided does not match the logged-in user."},
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

            return Response({"data": response.json()}, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

