from django.contrib.auth.models import AnonymousUser
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.authentication import JWTAuthentication
from google.oauth2 import id_token
from google.auth.transport import requests
from google.auth.exceptions import GoogleAuthError
from users.models import User


class GoogleJWTAuthentication(BaseAuthentication):
    def authenticate(self, request):
        token_header = request.headers.get("Authorization", "").split(" ")
        if len(token_header) != 2:
            return AnonymousUser(), None

        token_type, token = token_header

        if token_type != "Bearer":
            raise AuthenticationFailed("Invalid token type")

        try:
            # Attempt Google ID token validation
            id_info = id_token.verify_oauth2_token(token, requests.Request())
            email = id_info["email"]

            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                user = User.objects.create_user(
                    email=email,
                    first_names=id_info.get("given_name", ""),
                    last_names=id_info.get("family_name", "")
                )

            return user, token
        except (ValueError, KeyError, GoogleAuthError):
            # Google ID token validation failed
            # Attempt Simple JWT token validation
            jwt_auth = JWTAuthentication()
            return jwt_auth.authenticate(request)
