from django.conf import settings
from rest_framework import status, generics
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import Token, RefreshToken


class TokenObtainView(generics.GenericAPIView):
    permission_classes = [AllowAny]
    token_class = RefreshToken

    
    def get(self, request, *args, **kwargs):
        try:
            user = request.user
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        refresh = self.get_token(request.user)
        data = {
            'refresh': str(refresh),
            'access': str(refresh.access_token)

        }  
    
        response = Response()
        if data['access']:
            if settings.SIMPLE_JWT:
                response.set_cookie(
                    key = 'refresh_token',
                    value = refresh,
                    expires = settings.SIMPLE_JWT['REFRESH_TOKEN_LIFETIME'],
                    secure = settings.SIMPLE_JWT['AUTH_COOKIE_SECURE'],
                    httponly = settings.SIMPLE_JWT['AUTH_COOKIE_HTTP_ONLY'],
                    samesite = settings.SIMPLE_JWT['AUTH_COOKIE_SAMESITE'],
                    path = settings.SIMPLE_JWT['AUTH_COOKIE_PATH'],
                )

        del data['refresh']
        response.data = data
        response.status_code = status.HTTP_200_OK
        return response
    
    @classmethod
    def get_token(cls, user) -> Token:
        return cls.token_class.for_user(user)
