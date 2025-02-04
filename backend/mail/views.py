from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView
from rest_framework.exceptions import ValidationError


import os
from typing import Union
from urllib.parse import urlparse, unquote
from django.contrib.auth import get_user_model
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.core.mail import EmailMultiAlternatives
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_bytes
from cryptography.fernet import Fernet
from . safe_key import generate_safe_key
from .serializers import MailSerializer, LandlordMailSerializer
# from userauth.authentication import CustomAuthentication


User = get_user_model()
value = generate_safe_key()
cipher = Fernet(value)


def get_parsed_url_from_request(uri):
        return urlparse(uri)

def decrypt_token(token: str) -> str:
    """Decrypts the token and returns the user ID."""
    try:
        user_id = cipher.decrypt(force_bytes(token))
        return user_id.decode('utf-8')
    except Exception as e:
        raise Exception("Token could not be decrypted") from e

def get_user(user_id: str):
    """Fetches the user based on the user ID."""
    return User.objects.get(pk=user_id)



class sendAuthMail(APIView):
    serializer_class = MailSerializer
    permission_classes = [AllowAny]


    def post(self, request, *args, **kwargs):
        try:
            data = {'email': request.query_params.get('email'), 'mail_type': request.query_params.get('mail_type')}
            user = User.objects.get(email=data['email'])
            verification_token = default_token_generator.make_token(user) 
            encrypted_data = cipher.encrypt(force_bytes(user.pk))
            parsed_uri = get_parsed_url_from_request(request.build_absolute_uri())
            url_scheme = parsed_uri.scheme
            current_domain = parsed_uri.netloc
            if data['mail_type'] == 'password_reset':
                verification_link = f"{url_scheme}://{current_domain}/api/v1/password/reset/confirm/{verification_token}/{encrypted_data.decode()}" 
            else:
                verification_link = f"{url_scheme}://{current_domain}/api/v1/verify/{verification_token}/{encrypted_data.decode()}" 

            """Logic for sending mail, sends mail as plain text if html cannot be rendered"""
            html_message = render_to_string(f"{data['mail_type']}.html",
                                            {'username': user.first_name,
                                            'link': verification_link})                      
            plain_message = strip_tags(html_message) 
            subject = "Password Reset" if data['mail_type'] == 'password_reset' else "Verify your email"
            from_email, to = os.environ.get('EMAIL_HOST_USER'), user.email

            msg = EmailMultiAlternatives(subject, plain_message, from_email, [to])
            msg.attach_alternative(html_message, "text/html")
            msg.send()
        except ValidationError as e:
            return Response(e.messages, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response({"message": "E-mail has been sent" , "link": verification_link},
                        status= status.HTTP_200_OK)
    


class verifyAuthToken(APIView):
     serializer_class = MailSerializer
     permission_classes = [AllowAny]

     def post(self, request, *args, **kwargs):
        try:
            data = {'safe': request.query_params.get('safe'), 'token': request.query_params.get('token')}
            byte_user = unquote(data['safe'])
            user_id = decrypt_token(byte_user)
            user = get_user(user_id)
            match = default_token_generator.check_token(user, data['token'])
            if match:
                return Response({'email': user.email}, status=status.HTTP_200_OK)
    
            return Response({"error": "Invalid token"}, status=status.HTTP_400_BAD_REQUEST)
    
        except (User.DoesNotExist) as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": "An unexpected error occurred",
                            "details": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        

class LandlordContactMail(APIView):
    permission_classes = [AllowAny]
    custom``
    serializer_class = LandlordMailSerializer


    def post(self, request, *args, **kwargs):
        try:
            data = request.data
            serializer = self.serializer_class(data=data)
            serializer.is_valid(raise_exception=True)
            html_message = render_to_string('landlord_contact.html',
                                            {'name': data['name'],
                                            'email': data['email'],
                                            'message': data['message']})                      
            plain_message = strip_tags(html_message) 
            subject = "Landlord Contact"
            from_email, to = request.user.email, data.get('agentMail')

            msg = EmailMultiAlternatives(subject, plain_message, from_email, [to])
            msg.attach_alternative(html_message, "text/html")
            msg.send()
        except ValidationError as e:
            return Response(e.messages, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response({"message": "E-mail has been sent"},
                        status= status.HTTP_200_OK)