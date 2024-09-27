import os
from typing import Union
from django.contrib.auth.base_user import AbstractBaseUser
from dotenv import load_dotenv
from urllib.parse import urlparse
load_dotenv()
from django.core.exceptions import ValidationError
from django.contrib.sessions.backends.db import SessionStore
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.core.mail import EmailMultiAlternatives
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.contrib.auth import get_user_model
from django.utils.encoding import force_bytes
from cryptography.fernet import Fernet
from datetime import datetime, time


"""Finish modifying the token generator for password reset
and also check whether it is a valid action to take.
Then test it out in the views."""



User = get_user_model()
session = SessionStore()
session_key = None

# Variable to store the last key generation time
last_key_generation = None
key = None

def generate_key_if_midnight():
    global last_key_generation, key

    # Get the current time
    now = datetime.now()

    # Check if it's a new day (midnight)
    if last_key_generation is None or now.date() != last_key_generation.date():
        # Generate a new key
        current_key = Fernet.generate_key()
        last_key_generation = now

key = generate_key_if_midnight()
cipher = Fernet(key)

#I work on you today

class AccountActivationToken(PasswordResetTokenGenerator):
     ...

account_activation_token_generator = AccountActivationToken()

class CustomPasswordResetTokenGenerator(PasswordResetTokenGenerator):
     ...
     #Modify this function to alter what it returns
    #  def _make_hash_value(self, user: AbstractBaseUser, timestamp: int) -> str:
    #       return super()._make_hash_value(user, timestamp)

def get_parsed_url_from_request(uri):
        return urlparse(uri)


def send_email(request, user, **kwargs)-> Union[Response,None]:

    
    #Generate verification url for the email
    verification_token = account_activation_token_generator.make_token(user=user)
    encrypted_data = cipher.encrypt(force_bytes(user.pk))
    parsed_uri = get_parsed_url_from_request(request.build_absolute_uri())
    url_scheme = parsed_uri.scheme
    current_domain = parsed_uri.netloc
    verification_link = f"{url_scheme}://{current_domain}/api/v1/verify/{verification_token}/{encrypted_data.decode()}" 

    """Logic for sending mail alos sends mail as plain text incase html cannot be rendered"""
    html_message = render_to_string(f"{kwargs['mail_type']}.html",
                                    {'username': user.first_name,
                                    'link': verification_link})                      
    plain_message = strip_tags(html_message) 
    subject = "Password Reset" if kwargs['mail_type'] == 'password_reset' else "Verify your email"
    from_email, to = os.environ.get('EMAIL_HOST_USER'), user.email
    msg = EmailMultiAlternatives(subject, plain_message, from_email, [to])
    msg.attach_alternative(html_message, "text/html")
    # try:
    #     msg.send()
    # except ValidationError as e:
    #     return Response(e.messages, status=status.HTTP_400_BAD_REQUEST)

    return verification_link

    


def verify_token(token, safe) -> Union[Response, bool]:
    try:
          user_id = cipher.decrypt(force_bytes(safe))
          user = User.objects.get(pk=user_id.decode())
          match = account_activation_token_generator.check_token(user, token)
    except User.DoesNotExist as e:
         return Response({"error": "Link is invalid"}, status=status.HTTP_400_BAD_REQUEST)
    if match:
        return user