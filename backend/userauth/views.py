from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.exceptions import InvalidToken
from rest_framework.response import Response
from rest_framework.request import Request
from rest_framework import status, views, generics, permissions
from django.contrib.auth import get_user_model
from . serializers import (
    UserSignUpSerializer,
    UserPasswordResetSerializer,
    UserNewPasswordResetSerializer,
    UserLogoutSerializer,
    UserEmailVerificationSerializer,
    UserDetailSerializer,
    )
from utils.send_mail import send_email, verify_token, decrypt_token
from django.urls import reverse
from drf_spectacular.utils import extend_schema
from django.middleware import csrf
from django.conf import settings
from .authentication import CustomAuthentication
import requests
import os

User = get_user_model()

class VerifyEmailView(generics.GenericAPIView):
    permission_classes = [permissions.AllowAny]
    authentication_classes = [CustomAuthentication]
    serializer_class = UserEmailVerificationSerializer
    
    @extend_schema()
    def post(self, request: Request, *args, **kwargs):
        try:
            request_data = {'safe':kwargs['safe'], 'token': kwargs['token']}
            serializer = UserEmailVerificationSerializer(data=request_data)
            serializer.is_valid(raise_exception=True)
            data = serializer.validated_data
            response = requests.post(url=f"https://{request.get_host()}/{os.getenv("API_VERSION")}mail/verify-token/",
                                params={
                                    "safe": data["safe"],
                                    "token": data["token"]
                                },
                                verify=False)
            
            parsed_response = response.json()
            email = parsed_response.get('email')
            user = User.objects.filter(email=email).first()
            if isinstance(user, User):
                user.email_verified = True
                user.save(force_update= True, update_fields=["email_verified"])
                return Response({'detail':f"{user.username}, you email is successfully verified."})
        except Exception as e:
            return Response({'error': str(e), 'response': response}, status=status.HTTP_400_BAD_REQUEST)
        
        #If user instance returned is of type - None
        return Response({"error": "Nothing was returned"}, status=status.HTTP_400_BAD_REQUEST)




class CustomTokenObtainPairView(TokenObtainPairView):

    @extend_schema()
    def post(self, request: Request, *args, **kwargs) -> Response:

        email, password = request.data.get('email'), request.data.get('password')
        user = User.objects.filter(email=email).first()
        if not user:
            return Response({'error': 'Error getting user details', 'message': 'Invalid Email'},
                            status=status.HTTP_400_BAD_REQUEST)
        if not user.check_password(password):
            return Response({'error': 'Error getting user details', 'message': 'Invalid Password'},
                            status=status.HTTP_400_BAD_REQUEST)


        response = super().post(request, *args, **kwargs)
        if response.status_code == status.HTTP_200_OK:
            email = request.data.get('email')
            user = User.objects.get(email=email)
            if not user.email_verified:
                #Add logic to send mail if user is not verified
                link = send_email(request=request,user=user, mail_type='verify_on_login')
                return Response({"email": f"Sorry {user.username}, your email is not verified. "+
                                 "Please kindly check your mail to verify your account", "link":link}, status=status.HTTP_400_BAD_REQUEST)
        response.set_cookie(
                            key = settings.SIMPLE_JWT['AUTH_COOKIE'], 
                            value = response.data["refresh"],
                            expires = settings.SIMPLE_JWT['ACCESS_TOKEN_LIFETIME'],
                            secure = settings.SIMPLE_JWT['AUTH_COOKIE_SECURE'],
                            httponly = settings.SIMPLE_JWT['AUTH_COOKIE_HTTP_ONLY'],
                            samesite = settings.SIMPLE_JWT['AUTH_COOKIE_SAMESITE']
                            )

        if request.query_params.get("remember_me"):
            request.session.set_expiry(0)
        
        csrf.get_token(request)
        del response.data['refresh']
        response.data['user'] = user.username

        return response 
    

    
class CustomTokenRefreshView(TokenRefreshView):
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        if not request.data.get('refresh'):
            refresh_token = request.COOKIES.get("refresh")
            
            if not refresh_token:
                return Response({'error': 'Refresh token missing'}, status=status.HTTP_400_BAD_REQUEST)
            
            data = request.data.copy()
            data['refresh'] = refresh_token
            request._full_data = data

        try:
            response = super().post(request, *args, **kwargs)
            return response
        except InvalidToken:
            return Response({'error': 'Invalid token or token expired'}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        


class SignUpview(generics.CreateAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = UserSignUpSerializer

    @extend_schema()
    def create(self, request, *args, **kwargs):
        try:
            serializer = UserSignUpSerializer(data=request.data)
        
            serializer.is_valid(raise_exception=True)
            user = serializer.save()
            response = requests.post(url=f"https://{request.get_host()}/{os.getenv("API_VERSION")}mail/user-auth/",
                                    params={"mail_type": "signup", "email": serializer.validated_data['email']},
                                    verify=False)
            if response.status_code != 200:
                user.delete()
                return Response({"error": response}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
        return Response({"data": response.json()}, status=response.status_code)
    



class UserPasswordResetRequestView(views.APIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = UserPasswordResetSerializer
    
    @extend_schema()
    def post(self, request: Request, *args, **kwargs):
        if not request.user.is_authenticated:
            serializer = self.serializer_class(data=request.data)
            serializer.is_valid(raise_exception=True)
            user = User.objects.get(email=serializer.validated_data['email'])
        else:
            user = request.user

        link = send_email(request=request, user=user, mail_type='password_reset')
        
        return Response({'message': 'Kindly Check your mail to access the password reset link', "link": link},
                        status=status.HTTP_200_OK)
    
class VerifyPasswordResetView(generics.GenericAPIView):
    serializer_class = UserEmailVerificationSerializer
    permission_classes =  [permissions.AllowAny]
    
    def post(self, request, *args, **kwargs):

        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        user = verify_token(token=data['token'], safe=data['safe'])
        print(user)
        if isinstance(user, Response):
            return Response(user.data, status=user.status_code)
        if isinstance(user, User):
            return Response({'message':f"{user.username}, the link has been verified you can not reset your password.",
                             "reset link": reverse("userauth:new-password", kwargs={"safe": kwargs["safe"]})},
                             status=status.HTTP_200_OK)
        #If user instance returned is of type - None
        return Response({"error": "Invalid link or link expired"}, status=status.HTTP_400_BAD_REQUEST)



class UserPasswordResetConfirmView(generics.GenericAPIView):
    serializer_class = UserNewPasswordResetSerializer
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        user = User.objects.get(pk=decrypt_token(kwargs["safe"]))
        serializer = self.serializer_class(data=request.data, instance=user)
        print(serializer.instance)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        return Response({'message': 'User password successfully updated'}, status=status.HTTP_200_OK)


from django.contrib.auth import logout
class LogoutView(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [CustomAuthentication]
    serializer_class = UserLogoutSerializer

    @extend_schema()
    def post(self, request):
        if hasattr(request, 'session'):
            user = request.user
            response = Response({'message': f'{user.username} successfully logged out'}, status=status.HTTP_200_OK)
            logout(request)
            response.set_cookie(key='refresh', value="",path='/', httponly=True, samesite='None', secure=True, max_age=0)
            response.delete_cookie('csrftoken', path='/')

            
            return response
        return Response({'error': 'No session found'}, status=status.HTTP_400_BAD_REQUEST)

#Note you must change the permission to authenticated
class UserDetailView(generics.RetrieveAPIView):
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [CustomAuthentication]
    serializer_class = UserDetailSerializer

    def get_object(self):
        id = self.kwargs.get('pk')
        if id:
            queryset = get_user_model().objects.get(id=id)
        else:
            queryset = self.request.user
        return queryset