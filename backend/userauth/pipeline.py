import requests
from rest_framework_simplejwt.tokens import RefreshToken
from social_core.exceptions import AuthException


class InvalidToken(AuthException):

    def __str__(self):
        return "Access token verification failed"


def generate_jwt_for_user(user):
    refresh = RefreshToken.for_user(user)
    return {
        "access_token": str(refresh.access_token),
        "refresh_token": str(refresh),
        "_auth_user_id": str(user.pk),
        # "user": {
        #     "id": user.id,
        #     "email": user.email,
        #     "name": user.get_full_name(),
        # },
    }


def validate_token(access):
    url = f"https://www.googleapis.com/oauth2/v3/tokeninfo?access_token={access}"
    response = requests.get(url=url)
    if response.status_code == 200:
        return response.json()
    raise InvalidToken


def save_tokens(backend, user, response, *args, **kwargs):
    """Save the access and refresh tokens from the provider."""
    if backend.name == "google-oauth2":
        try:
            social = user.social_auth.get(provider=backend.name)
            access_token = response.get("access_token")
            refresh_token = response.get("refresh_token")
            expires_in = response.get("expires_in")

            if validate_token(access_token):
                social.extra_data["access_token"] = access_token
                if refresh_token:
                    social.extra_data["refresh_token"] = refresh_token
                social.extra_data["expires_in"] = expires_in
                social.save()
        except Exception as e:
            return {"error": str(e)}


def generate_jwt_token(strategy, backend, user, *args, **kwargs):
    if user and user.is_active:
        token_data = generate_jwt_for_user(user)

        strategy.session_set("jwt_data", token_data)

        return {"token_data": token_data}
