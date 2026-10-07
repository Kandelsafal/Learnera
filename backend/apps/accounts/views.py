from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import UserRegistrationSerializer, UserSerializer, UserLoginSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from .models import RefreshSession
from datetime import datetime
from django.utils import timezone
from django.db import transaction
# Create your views here.

class UserRegistrationView(APIView):

    def post(self, request):
        serializer = UserRegistrationSerializer(data = request.data)

        if serializer.is_valid():
            user = serializer.save()

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

            expires_at = datetime.fromtimestamp(
                    token["exp"],
                    tz=timezone.get_current_timezone()
            )
            #Create Refresh Session
            RefreshSession.objects.create(
                user = user,
                token_jti = str(token["jti"]),
                expires_at = expires_at
            )
            response = Response(
                {   
                    "message":"Login Sucessful",
                    "user":UserSerializer(user).data,
                    #Access Token
                    "access_token":str(token.access_token)

                },
                status=status.HTTP_200_OK
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

class LogoutView(APIView):
    def post(self, request):
        response = Response(
            {
                "message": "Logout Successfully",
                
            }
            ,status=status.HTTP_200_OK
        
        )
        response.delete_cookie('refresh')
        return response

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
                        "access_token":str(new_refresh_token.access_token)
                    },
                    status= status.HTTP_201_CREATED
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

