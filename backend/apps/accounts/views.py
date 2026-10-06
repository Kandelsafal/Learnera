from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import UserRegistrationSerializer, UserSerializer, UserLoginSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
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
            token = RefreshToken.for_user(user)

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
            new_token = RefreshToken(refreshed_token)
            print("NEW TOKEN", new_token)
            response = Response(
                {
                    "message": "New Token Generated",
                    "access_token":str(new_token.access_token)
                },
                status= status.HTTP_201_CREATED
            )
            response.set_cookie(
                key="refresh_token",
                value=str(new_token),
                httponly=True,
                secure=False,  # True in production with HTTPS
                samesite="Lax", 
            )
            return response

        except TokenError :
            return Response(
                {
                    "error": "Invalid or expired refresh token"
                }, 
                status=status.HTTP_401_UNAUTHORIZED
                )

