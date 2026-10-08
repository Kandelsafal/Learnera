from django.test import TestCase

from apps.accounts.models import User
from apps.accounts.serializers import UserLoginSerializer, UserRegistrationSerializer, UserSerializer

class UserSerializerTestCase(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            email="john@example.com",
            password="securepassword123",
            first_name="John",
            last_name="Doe",
            phn_number="9812345678"
        )

    def test_user_serializer(self):
        serializer = UserSerializer(self.user)

        self.assertEqual(
            serializer.data["email"],
            "john@example.com"
        )

        self.assertEqual(
            serializer.data["first_name"],
            "John"
        )

        self.assertNotIn(
            "password",
            serializer.data
        )

class UserRegistrationSerializerTestCase(TestCase):
    def test_user_registartion(self):
        data = {
              "first_name": "Jane",
            "last_name": "Doe",
            "email": "jane@example.com",
            "phn_number": "9800000000",
            "password": "securepassword123"
        }

        serializer = UserRegistrationSerializer(data=data)

        self.assertTrue(serializer.is_valid(), serializer.errors)

        user = serializer.save()

        self.assertEqual(user.email, "jane@example.com")
        self.assertTrue(
            user.check_password("securepassword123")
        )
        self.assertNotIn("password", serializer.data)

class UserLoginSerializerTestCase(TestCase):
     def test_user_login(self):
        User.objects.create_user(
            email="jane@example.com",
            password="securepassword123",
            first_name="Jane",
            last_name="Doe",
            is_email_verified=True
        )
        
        data = {
            "email": "jane@example.com",
            "password": "securepassword123"
        }
    
        serializer = UserLoginSerializer(data=data)
    
        self.assertTrue(serializer.is_valid(), serializer.errors)
    
        
        user = serializer.validated_data["user"]
    
        # 4. Assertions
        self.assertEqual(user.email, "jane@example.com")
        self.assertTrue(user.check_password("securepassword123"))
    
    