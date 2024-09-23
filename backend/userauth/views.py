from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.response import Response
from rest_framework.request import Request
from rest_framework import status, views, generics, permissions
from django.contrib.auth import get_user_model
from . serializers import (
    UserSignUpSerializer,
    UserPasswordResetSerializer,
    UserLogoutSerializer,
    UserEmailVerificationSerializer)
from utils.send_mail import send_email, verify_token
from drf_spectacular.utils import extend_schema


User = get_user_model()

class VerifyEmailView(generics.GenericAPIView):
    serializer_class = UserEmailVerificationSerializer
    
    def post(self, request: Request, *args, **kwargs):
        serializer = UserEmailVerificationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        response = verify_token(token=data['token'], safe=data['safe'])
        if isinstance(response, Response):
            return response
        


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


class SignUpview(generics.CreateAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = UserSignUpSerializer

    @extend_schema()
    def create(self, request, *args, **kwargs):
        serializer = UserSignUpSerializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        user =serializer.save()
        #Implement logic to send mail for user email verification
        response = send_email(request=request, user=user, mail_type='signup')
        if isinstance(response, Response):
            return response

        return Response({"message": f"{user.first_name}, your account has been successfully created." +
                         "Check your mail to verify your account"},
                        status=status.HTTP_200_OK)


class UserPasswordResetView(views.APIView):
    
    def post(self, request: Request, *args, **kwargs):
        if request.user.is_authenticated:
            user = User.objects.get(email=serializer.validated_data['email'])
            send_email(request=request,user=user, mail_type='password_reset')
            return Response({'message': f'{user.username}, please your mail to access the password reset link'},
                        status=status.HTTP_200_OK)

        serializer = UserPasswordResetSerializer(data=request.data)
        user = User.objects.get(email=serializer.validated_data['email'])
        send_email(request=request,user=user, mail_type='password_reset')

        return Response({'message': 'Kindly Check your mail to access the password reset link'},
                        status=status.HTTP_200_OK)



class LogoutView(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = UserLogoutSerializer

    @extend_schema()
    def post(self, request):
        if hasattr(request, 'session'):
            session = request.session
            user = request.user
            session.flush()
            return Response({'message':f'{user.username} successfully logged out'}) 