
from django.test import TestCase
from rest_framework import status
from django.contrib.auth import get_user_model
User = get_user_model()
class UserRegistrationAPITest(TestCase):
    def test_user_can_register(self):
        data = {
            "first_name": "Jane",
            "last_name": "Doe",
            "email": "jane@example.com",
            "phn_number": "9800000000",
            "password": "securepassword123",
        }
        response = self.client.post(
            "/api/accounts/register/",
            data,
            format="json"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED
        )

        self.assertEqual(
            response.data["email"],
            "jane@example.com"
        )

        self.assertNotIn("password", response.data)

        user = User.objects.get(
            email="jane@example.com"
        )

        self.assertTrue(
            user.check_password("securepassword123")
        )


    def test_duplicate_email_is_rejected(self):
        User.objects.create_user(
            first_name="Existing",
            last_name="User",
            email="jane@example.com",
            password="securepassword123",
        )

        data = {
            "first_name": "Jane",
            "last_name": "Doe",
            "email": "jane@example.com",
            "phn_number": "9811111111",
            "password": "anotherpassword123",
        }

        response = self.client.post(
            "/api/accounts/register/",
            data,
            format="json"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST
        )

    def test_registration_requires_email(self):
        data = {
            "first_name": "Jane",
            "last_name": "Doe",
            "password": "securepassword123",
        }

        response = self.client.post(
            "/api/accounts/register/",
            data,
            format="json"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST
        )

        self.assertIn(
            "email",
            response.data
        )