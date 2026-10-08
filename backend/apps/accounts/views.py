import secrets

from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import ResetPasswordSerializer, UserRegistrationSerializer, UserSerializer, UserLoginSerializer, ChangePasswordSerializer,SessionViewSerializer, EmailVerificationSerializer, ForgotPasswordSerializer, ResendVerificationSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from .models import PasswordResetToken, RefreshSession
from datetime import datetime
from django.utils import timezone
from django.db import transaction
from rest_framework.permissions import IsAuthenticated
from .models import EmailVerificationToken
from .utils import generate_email_verification_token, generate_password_verification_token, get_device_name
from django.contrib.auth import get_user_model
from datetime import timedelta
import hashlib
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect, ensure_csrf_cookie
# Create your views here.
@method_decorator(ensure_csrf_cookie, name="dispatch")
class CSRFTokenView(APIView):

    def get(self, request):

        return Response(
            {"message": "CSRF cookie set."},
            status=status.HTTP_200_OK
        )

@method_decorator(csrf_protect, name="dispatch")
class CSRFTestView(APIView):

    def post(self, request):
        return Response(
            {"message": "CSRF validation passed!"},
            status=status.HTTP_200_OK
        )

class UserRegistrationView(APIView):

    def post(self, request):
        serializer = UserRegistrationSerializer(data = request.data)

        if serializer.is_valid():
            user = serializer.save()

            raw_token, token_hash = generate_email_verification_token()
            print("Email Verification token",raw_token)
            EmailVerificationToken.objects.create(
                user = user,
                token_hash = token_hash,
                expires_at = timezone.now() + timedelta(
                    minutes = 15
                )
            )

            return Response(
                {   
                    "message":"Registration Sucessfull",
                    "user":UserSerializer(user).data,
                },
                status = status.HTTP_201_CREATED
            )

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )

class VerifyEmailView(APIView):

    def post(self, request):

        serializer = EmailVerificationSerializer(
            data=request.data
        )

        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )

        raw_token = serializer.validated_data["token"]

        token_hash = hashlib.sha256(
            raw_token.encode()
        ).hexdigest()

        try:

            with transaction.atomic():

                verification_token = (
                    EmailVerificationToken.objects
                    .select_for_update()
                    .select_related("user")
                    .get(token_hash=token_hash)
                )

                if verification_token.used_at is not None:
                    return Response(
                        {
                            "error": "Verification token has already been used."
                        },
                        status=status.HTTP_400_BAD_REQUEST
                    )

                if verification_token.expires_at <= timezone.now():
                    return Response(
                        {
                            "error": "Verification token has expired."
                        },
                        status=status.HTTP_400_BAD_REQUEST
                    )

                user = verification_token.user

                user.is_email_verified = True
                user.save(
                    update_fields=["is_email_verified"]
                )

                verification_token.used_at = timezone.now()
                verification_token.save(
                    update_fields=["used_at"]
                )

                return Response(
                    {
                        "message": "Email verified successfully."
                    },
                    status=status.HTTP_200_OK
                )

        except EmailVerificationToken.DoesNotExist:

            return Response(
                {
                    "error": "Invalid verification token."
                },
                status=status.HTTP_400_BAD_REQUEST
            )

class ResendVerificationView(APIView):

    def post(self, request):
        serializer  = ResendVerificationSerializer(
            data = request.data
        )

        if not serializer.is_valid():
            return Response(
                            serializer.errors,
                            status=status.HTTP_400_BAD_REQUEST
                        )
        
        email = serializer.validated_data["email"]
        User = get_user_model()

        user = User.objects.filter(
            email = email
        ).first()

        if not user :
            return Response(
               {
                   "message": (
                        "If an account exists with this email, "
                        "a verification email has been sent."
                    )
                },
                status=status.HTTP_200_OK,
            )

        if user.is_email_verified:
            return Response(
                {
                    "message": "Email is already verified."
                },
                status=status.HTTP_200_OK,
            )
        with transaction.atomic():

            EmailVerificationToken.objects.filter(
                user = user,
                used_at__isnull=True,
                ).update(
                    used_at=timezone.now()
            )

            raw_token , token_hash = generate_email_verification_token()

            expires_at = timezone.now() + timedelta(minutes=20)
            EmailVerificationToken.objects.create(
            user=user,
            token_hash=token_hash,
            expires_at=expires_at,
            )
            print("Resend Verification", raw_token)
        return Response(
            {
                "message": (
                    "If an account exists with this email, "
                    "a verification email has been sent."
                )
            },
            status=status.HTTP_200_OK,
        )

class LoginView(APIView):
    def post(self, request):
        serializer = UserLoginSerializer(
            data = request.data
        )

        if serializer.is_valid():
            #Retrieve the Validated User Data
            user = serializer.validated_data["user"]
            #Generate Token
            token = RefreshToken.for_user(user)
            token["token_version"] = user.token_version
            expires_at = datetime.fromtimestamp(
                    token["exp"],
                    tz=timezone.get_current_timezone()
            )
            #Create Refresh Session
            user_agent = request.META.get("HTTP_USER_AGENT")
            RefreshSession.objects.create(
                user = user,
                token_jti = str(token["jti"]),
                ip_address=request.META.get("REMOTE_ADDR"),
                user_agent=user_agent,
                device_name=get_device_name(user_agent),
                expires_at = expires_at
            )
            response = Response(
                {   
                    "message":"Login Sucessful",
                    "user":UserSerializer(user).data,
                   

                },
                status=status.HTTP_200_OK
            )
             # Set access token cookie
            response.set_cookie(
                key="access_token",
                value=str(token.access_token),
                httponly=True,
                secure=False,  # True in production with HTTPS
                samesite="Lax",
            )
            #Set COOKIE For Refresh Token
            response.set_cookie(
                key="refresh_token",
                value=str(token),
                httponly=True,
                secure=False,  # True in production with HTTPS
                samesite="Lax", 
            )

            return response

            
        
        return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
        )

@method_decorator(csrf_protect, name="dispatch")
class LogoutView(APIView):
    def post(self, request):
        cookieSession = request.COOKIES.get("refresh_token")
        if not cookieSession:
            return Response(
                {"error": "Refresh token not found"},
                status=status.HTTP_401_UNAUTHORIZED
            )
        try:
            token = RefreshToken(cookieSession)
            token_jti = str(token["jti"])
            with transaction.atomic():
                session = RefreshSession.objects.select_for_update().get(token_jti = token_jti)
                session.revoked_at = timezone.now()
                session.last_used_at = timezone.now()

                session.save(
                    update_fields=[
                        "revoked_at",
                        "last_used_at"
                    ]
                )
                User = get_user_model()
                user = User.objects.get(id=session.user_id)
                user.last_login = timezone.now()
                user.save(
                    update_fields=["last_login"]
                )
            response = Response(
                {
                    "message": "Logout Successful"
                },
                status=status.HTTP_200_OK
            )

            # Remove refresh token from browser
            response.delete_cookie(
                "refresh_token",
                "access_token"
            )

            return response

        except RefreshSession.DoesNotExist:
            return Response(
                {"error": "Refresh session not found"},
                status=status.HTTP_401_UNAUTHORIZED
            )

        except TokenError:
            return Response(
                {"error": "Invalid or expired refresh token"},
                status=status.HTTP_401_UNAUTHORIZED
            )

@method_decorator(csrf_protect, name="dispatch")
class LogoutAllView(APIView):

    def post(self, request):

        # Get refresh token from cookie
        refresh_token = request.COOKIES.get("refresh_token")

        if not refresh_token:
            return Response(
                {
                    "error": "Refresh token not found"
                },
                status=status.HTTP_401_UNAUTHORIZED
            )

        try:
            # Decode and validate refresh token
            decoded_token = RefreshToken(refresh_token)

            # Get JTI
            decoded_token_jti = str(
                decoded_token["jti"]
            )

            with transaction.atomic():

                # Find current refresh session
                current_user_session = (
                    RefreshSession.objects
                    .select_for_update()
                    .get(
                        token_jti=decoded_token_jti,
                        
                    )
                )
                if current_user_session.revoked_at is not None:
                    return Response(
                        {"error": "Refresh session has been revoked"},
                        status=status.HTTP_401_UNAUTHORIZED
                    )

                # Get user ID from the session
                current_user = current_user_session.user

                # Revoke all active sessions for this user
                RefreshSession.objects.filter(
                    user=current_user,
                    revoked_at__isnull=True
                ).select_for_update().update(
                    revoked_at=timezone.now(),
                    last_used_at=timezone.now()
                )
                User = get_user_model()
                user = User.objects.get(id=current_user.id)
                user.last_login = timezone.now()
                user.save(
                    update_fields=["last_login"]
                    )

            response = Response(
                {
                    "message": "Logged out from all sessions"
                },
                status=status.HTTP_200_OK
            )

            # Remove current browser's refresh token
            response.delete_cookie(
                "refresh_token",
                "access_token"
            )

            return response

        except RefreshSession.DoesNotExist:
            return Response(
                {
                    "error": "Refresh session not found"
                },
                status=status.HTTP_401_UNAUTHORIZED
            )

        except TokenError:
            return Response(
                {
                    "error": "Invalid or expired refresh token"
                },
                status=status.HTTP_401_UNAUTHORIZED
            )

@method_decorator(csrf_protect, name="dispatch")
class RefreshTokenView(APIView):
    def post(self, request):
        #Read Token from cookies
        refreshed_token = request.COOKIES.get('refresh_token')

        if not refreshed_token:
            return Response(
                {"error": "Refresh token not found"}, 
                status=status.HTTP_401_UNAUTHORIZED
            )

        try:
            token = RefreshToken(refreshed_token)
            
            #Check Session
            token_jti = str(token["jti"])

            with transaction.atomic():
                session = RefreshSession.objects.select_for_update().get(
                    token_jti = token_jti
                )
                
                # 5. Check whether the session was revoked
                if session.revoked_at is not None:
                    return Response(
                        {"error": "Refresh session has been revoked"},
                        status=status.HTTP_401_UNAUTHORIZED
                    )

                # 6. Check database-side expiration
                if session.expires_at <= timezone.now():
                    return Response(
                        {"error": "Refresh session has expired"},
                        status=status.HTTP_401_UNAUTHORIZED
                    )

                token_version = token.get("token_version")
                if token_version is None:
                    return Response(
                        {"error": "Token version is missing"},
                        status=status.HTTP_401_UNAUTHORIZED
                    )
                
                if token_version != session.user.token_version:
                    return Response(
                    {"error": "Refresh token has been invalidated"},
                    status=status.HTTP_401_UNAUTHORIZED
                )

                session.last_used_at = timezone.now()
                session.revoked_at = timezone.now()
                session.save(
                                    update_fields=[
                                        "last_used_at",
                                        "revoked_at"
                                        ]
                                )
                #New Token Generated
                new_refresh_token = RefreshToken.for_user(session.user)
                new_refresh_token["token_version"] = session.user.token_version

                expires_at = datetime.fromtimestamp(
                                    new_refresh_token["exp"],
                                    tz=timezone.get_current_timezone()
                            )

                
                RefreshSession.objects.create(
                    user = session.user,
                    token_jti = str(new_refresh_token["jti"]),
                    expires_at = expires_at
                )

                response = Response(
                    {
                        "message": "New Token Generated",
                     
                    },
                    status= status.HTTP_201_CREATED
                )
                response.set_cookie(
                                    key="access_token",
                                    value=str(new_refresh_token.access_token),
                                    httponly=True,
                                    secure=False,  # True in production with HTTPS
                                    samesite="Lax", 
                                )
                response.set_cookie(
                    key="refresh_token",
                    value=str(new_refresh_token),
                    httponly=True,
                    secure=False,  # True in production with HTTPS
                    samesite="Lax", 
                )
                return response
        except RefreshSession.DoesNotExist:
            return Response(
                {"error": "Invalid refresh session."},
                status=status.HTTP_401_UNAUTHORIZED
            )
            
        except TokenError :
            return Response(
                {
                    "error": "Invalid or expired refresh token"
                }, 
                status=status.HTTP_401_UNAUTHORIZED
                )


class MeView(APIView):
    permission_classes= [IsAuthenticated]
    def get(self, request):
        serializer = UserSerializer(request.user)

        return Response(
               serializer.data 
        ,status=status.HTTP_200_OK
        )

    def patch(self, request):
        serializer = UserSerializer(request.user, data = request.data, partial = True)

        if serializer.is_valid():
            serializer.save()

            return Response(
                serializer.data,
                status=status.HTTP_200_OK
            )

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )

@method_decorator(csrf_protect, name="dispatch")
class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request):

        serializer = ChangePasswordSerializer(
            data = request.data,
            context = {"request":request}
        )
        if serializer.is_valid():
            user = request.user

           
            
            with transaction.atomic():
                user.set_password(
                                serializer.validated_data["new_password"]
                            )
                user.token_version += 1
                
                user.save(
                                            update_fields = [
                                                "password",
                                                "token_version"
                                                ]
                                            )
                RefreshSession.objects.filter(
                    user = user,
                    revoked_at__isnull = True,

                ).select_for_update().update(
                    revoked_at = timezone.now(),
                    last_used_at = timezone.now()
                )
                

            return Response(
                {
                    "message": "Password changed successfully."
                },
                status=status.HTTP_200_OK
            )
        
        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )

class ForgotPasswordView(APIView):
    

    def post(self, request):
        serializer = ForgotPasswordSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST,
            )
        email = serializer.validated_data["email"]
        User = get_user_model()
        user = User.objects.filter(
            email = email
        ).first()

        
        if not user:
            return Response(
                {
                    "message": (
                        "If an account exists with this email, "
                        "a password reset link has been sent."
                    )
                },
                status=status.HTTP_200_OK,
            )
        
        raw_token, token_hash = generate_password_verification_token()
        expires_at = timezone.now() + timedelta(minutes=15)

        print("RAW PASSWORD TOKEN : ",raw_token)
        
        PasswordResetToken.objects.create(
            user=user,
            token_hash=token_hash,
            expires_at=expires_at,
        )

        return Response(
            {
                "message": (
                    "If an account exists with this email, "
                    "a password reset link has been sent."
                )
            },
            status=status.HTTP_200_OK,
        )

class ResetPasswordView(APIView):
    def post(self, request):
        serializer = ResetPasswordSerializer(
            data = request.data
        )

        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST,
            )

        

        raw_token = serializer.validated_data["token"]

        token_hash = hashlib.sha256(
            raw_token.encode()
        ).hexdigest()

        with transaction.atomic():
            try:

                reset_token = PasswordResetToken.objects.select_for_update().get(
                    token_hash=token_hash
                )

            except PasswordResetToken.DoesNotExist:

                return Response(
                    {"error": "Invalid or expired reset token."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Check whether token has already been used
            if reset_token.used_at is not None:

                return Response(
                    {"error": "Invalid or expired reset token."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Check expiration
            if reset_token.expires_at <= timezone.now():

                return Response(
                    {"error": "Invalid or expired reset token."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Change password
            user = reset_token.user

            user.set_password(
                serializer.validated_data["new_password"]
            )

            user.save(
                update_fields=["password"]
            )

            # Mark reset token as used
            reset_token.used_at = timezone.now()

            reset_token.save(
                update_fields=["used_at"]
            )

            # Revoke all active sessions
            RefreshSession.objects.filter(
                user=user,
                revoked_at__isnull=True,
            ).update(
                revoked_at=timezone.now(),
                last_used_at= timezone.now(),
            )

        return Response(
            {
                "message": "Password reset successfully."
            },
            status=status.HTTP_200_OK,
        )

class SessionsView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):

        sessions = RefreshSession.objects.filter(
            user = request.user,
            revoked_at__isnull = True,
            expires_at__gt=timezone.now(),
        ).order_by("-created_at")
        serializer = SessionViewSerializer( sessions,
            many=True,)

        return Response(
            {
                "sessions": serializer.data,
            },
            status=status.HTTP_200_OK,
        )

class RevokeSessionView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, session_id):

        session = RefreshSession.objects.filter(
            id=session_id,
            user=request.user,
            revoked_at__isnull=True,
        ).first()

        if not session:
            return Response(
                {
                    "error": "Session not found or already revoked."
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        session.revoked_at = timezone.now()
        session.last_used_at = timezone.now()

        session.save(
            update_fields=["revoked_at", "last_used_at"]
        )

        return Response(
            {
                "message": "Session revoked successfully."
            },
            status=status.HTTP_200_OK,
        )