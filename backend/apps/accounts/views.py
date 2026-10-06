from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import UserRegistrationSerializer, UserSerializer, UserLoginSerializer
from rest_framework_simplejwt.tokens import RefreshToken
# Create your views here.

class UserRegistrationView(APIView):

    def post(self, request):
        serializer = UserRegistrationSerializer(data = request.data)

        if serializer.is_valid():
            user = serializer.save()

            return Response(
                UserSerializer(user).data,
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

            return Response(
                UserSerializer(user).data,
                status=status.HTTP_200_OK
            )
        
        return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
        )