from rest_framework.generics import GenericAPIView
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from userauth.authentication import CustomAuthentication

class StartPaymentView(GenericAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = CustomAuthentication

    def post(self, request, *args, **kwargs):
        pass