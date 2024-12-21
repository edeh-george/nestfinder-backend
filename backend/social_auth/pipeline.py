import requests
from social_core.exceptions import AuthException
from django.http import HttpResponse
from django.conf import settings
from rest_framework import status
from rest_framework.response import Response


class InvalidToken(AuthException):

    def __str__(self):
        return "Access token verification failed"



def validate_token(access):
    url = f"https://www.googleapis.com/oauth2/v3/tokeninfo?access_token={access}"
    response = requests.get(url=url)
    if response.status_code == 200:
        return response.json()
    raise InvalidToken

def save_tokens(backend, user, response, *args, **kwargs):
    """Save the access and refresh tokens from the provider."""
    if backend.name == 'google-oauth2':
        try:
            social = user.social_auth.get(provider=backend.name)
            access_token = response.get('access_token')
            refresh_token = response.get('refresh_token')
            expires_in = response.get('expires_in')

            if validate_token(access_token):
                social.extra_data['access_token'] = access_token
                if refresh_token:
                    social.extra_data['refresh_token'] = refresh_token
                social.extra_data['expires_in'] = expires_in
                social.save()
        except Exception as e:
            return {'error': str(e)}
        



def store_token_in_cookies(backend, user, response, *args, **kwargs):
    response = kwargs.get('response', HttpResponse())
    social = user.social_auth.filter(provider=backend.name).order_by('id').first()
    access_token = social.extra_data.get('access_token')

    if access_token:
        if settings.SIMPLE_JWT:
            response.set_cookie(
                key = 'google_access_token',
                value = access_token,
                exprires = settings.SIMPLE_JWT['ACCESS_TOKEN_LIFETIME'],
                secure = settings.SIMPLE_JWT['AUTH_COOKIE_SECURE'],
                httponly = settings.SIMPLE_JWT['AUTH_COOKIE_HTTP_ONLY'],
                samesite = settings.SIMPLE_JWT['AUTH_COOKIE_SAMESITE'],
                path = settings.SIMPLE_JWT['AUTH_COOKIE_PATH'],
            )
         