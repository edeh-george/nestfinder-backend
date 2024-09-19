from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.response import Response
from rest_framework.request import Request
from rest_framework import status, views
from django.contrib.auth import get_user_model
from . serializers import (
    UserSignUpSerializer,
    UserPasswordResetSerializer)


User = get_user_model()

class CustomTokenObtainPairView(TokenObtainPairView):
    def post(self, request: Request, *args, **kwargs) -> Response:

        response = super().post(request, *args, **kwargs)
        if response.status_code == status.HTTP_200_OK:
            email = request.data.get('email')
            user = User.objects.get(email=email)
            if not user.email_verified:
                #Add logic to send mail if user is not verified
                return Response({"email": f"Sorry {user.username}, your email is not verified. "+
                                 "Please kindly check your mail to verify your account"}, status=status.HTTP_400_BAD_REQUEST)
            return response      


class SignUpview(views.APIView):
    # serializer_class = UserSignUpSerializer

    def post(self, request: Request, *args, **kwargs):
        serializer = UserSignUpSerializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
        user =serializer.save()
        #Implement logic to send mail for user email verification

        return Response({"message": f"{user.first_name}, your account has been successfully created."},
                        status=status.HTTP_200_OK)


class UserPasswordResetView(views.APIView):
    

    def post(self, request: Request, *args, **kwargs):
        serializer = UserPasswordResetSerializer(data=request.data)
        user = User.objects.get(email=serializer.validated_data['email'])
        #finish up the password reset
        
