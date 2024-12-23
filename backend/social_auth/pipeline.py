import requests
from social_core.exceptions import AuthException


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
        




         