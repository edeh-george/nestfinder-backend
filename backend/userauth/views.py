from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.response import Response
from rest_framework.request import Request
from rest_framework import status, views, generics, permissions
from django.contrib.auth import get_user_model
from . serializers import (
    UserSignUpSerializer,
    UserPasswordResetSerializer,
    UserPasswordResetLoggedinSerializer,
    UserLogoutSerializer,
    UserEmailVerificationSerializer)
from utils.send_mail import send_email, verify_token
from drf_spectacular.utils import extend_schema


User = get_user_model()

class VerifyEmailView(generics.GenericAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = UserEmailVerificationSerializer
    
    @extend_schema()
    def post(self, request: Request, *args, **kwargs):
        serializer = UserEmailVerificationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        user = verify_token(token=data['token'], safe=data['safe'])
        if isinstance(user, User):
            user.email_verified = True
            user.save(force_update= True, update_fields=["email_verified"])
            return Response({'detail':f"{user.username}, you email is successfully verified."})
        
        #If user instance returned is of type - None
        return Response({"error": "Nothing was returned"}, status=status.HTTP_400_BAD_REQUEST)




class CustomTokenObtainPairView(TokenObtainPairView):

    @extend_schema()
    def post(self, request: Request, *args, **kwargs) -> Response:

        response = super().post(request, *args, **kwargs)
        if response.status_code == status.HTTP_200_OK:
            email = request.data.get('email')
            user = User.objects.get(email=email)
            if not user.email_verified:
                #Add logic to send mail if user is not verified
                link = send_email(request=request,user=user, mail_type='verify_on_login')
                return Response({"email": f"Sorry {user.username}, your email is not verified. "+
                                 "Please kindly check your mail to verify your account", "link":link}, status=status.HTTP_400_BAD_REQUEST)
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

class VerifyPasswordResetView(generics.GenericAPIView):
    ...

class UserPasswordResetRequestView(views.APIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = UserPasswordResetSerializer
    
    @extend_schema()
    def post(self, request: Request, *args, **kwargs):
        user = request.user

        if not user.is_authenticated:
            serializer = UserPasswordResetConfirmView(data=request.data)
            serializer.is_valid(raise_exception=True)
            user = User.objects.get(email=serializer.validated_data['email'])

        link = send_email(request=request, user=request.user, mail_type='password_reset')
        
        return Response({'message': 'Kindly Check your mail to access the password reset link', "link": link},
                        status=status.HTTP_200_OK)

class UserPasswordResetConfirmView(generics.GenericAPIView):
    ...

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