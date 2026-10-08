from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.exceptions import AuthenticationFailed


class VersionedJWTAuthentication(JWTAuthentication):
    def authenticate(self, request):

        # Get access token from HttpOnly cookie
        access_token = request.COOKIES.get("access_token")

        # No access token → unauthenticated request
        if not access_token:
            return None

        # Validate the JWT using SimpleJWT
        validated_token = self.get_validated_token(
            access_token
        )

        # Get user + perform token version check
        user = self.get_user(validated_token)

        return (user, validated_token)
      
    def get_user(self, validated_token):
        user = super().get_user(validated_token)

        token_version = validated_token.get("token_version")

        if token_version is None:
            raise AuthenticationFailed(
                "Token version is missing."
            )

        if token_version != user.token_version:
            raise AuthenticationFailed(
                "Token has been invalidated."
            )

        return user
