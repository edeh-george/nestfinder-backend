from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend

User = get_user_model()


class EmailBackend(ModelBackend):
    """
    Custom authentication backend to authenticate users using their email and password.
    """

    def authenticate(self, request, username=None, password=None, **kwargs):
        # Use 'username' as 'email'
        email = kwargs.get("email") or username
        try:
            user = User.objects.get(email=email)
            if not user:
                user = User.objects.get(username=email)
        except User.DoesNotExist:
            return None

        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
