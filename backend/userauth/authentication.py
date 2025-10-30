import os

import requests
from django.conf import settings
from rest_framework import exceptions
from rest_framework.authentication import CSRFCheck
from rest_framework_simplejwt.authentication import JWTAuthentication


def enforce_csrf(request):
    """
    Enforce CSRF validation.
    """
    check = CSRFCheck(lambda x: None)
    # populates request.META['CSRF_COOKIE'], which is used in process_view()
    check.process_request(request)
    reason = check.process_view(request, None, (), {})
    if reason:
        # CSRF failed, bail with explicit error message
        raise exceptions.PermissionDenied("CSRF Failed: %s" % reason)


def get_access_token(refresh, request):
    url = f'{request.scheme}://{request.get_host()}/{os.getenv("API_VERSION")}token/refresh/'
    response = requests.post(url=url, data={"refresh": refresh}, verify=False)
    if response.status_code == 200:
        response_data = response.json()
        return response_data.get("access")
    else:
        exceptions.AuthenticationFailed("Failed to refresh access token")


class CustomAuthentication(JWTAuthentication):

    def authenticate(self, request):
        header = self.get_header(request)

        if header is None:
            raw_token = request.COOKIES.get(settings.SIMPLE_JWT["AUTH_COOKIE"]) or None
        else:
            raw_token = self.get_raw_token(header)
        if raw_token is None:
            return None
        try:
            validated_token = self.get_validated_token(
                get_access_token(raw_token, request)
            )
        except exceptions.AuthenticationFailed as e:
            raise exceptions.AuthenticationFailed(
                {"error": "token validation failed", "message": str(e)}
            )
        enforce_csrf(request)
        return self.get_user(validated_token), validated_token
