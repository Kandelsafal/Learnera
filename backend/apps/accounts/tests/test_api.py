
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
        print("RESPONSE DATA:", response.data)
        self.assertEqual(
            response.data["user"]["email"],
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

class UserLoginAPITest(TestCase):
    def setUp(self):
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

    def test_user_can_login(self):
       
        login_data = {
            "email":"jane@example.com",
            "password":"securepassword123"
        }
        response = self.client.post(
                            "/api/accounts/login/",
                            login_data,
                            format="json"
                        )
        
        self.assertEqual(
                    response.status_code,
                    status.HTTP_200_OK
                        )

        self.assertIn(
            "access_token", response.data
        )

    def test_login_with_wrong_password(self):
            login_data = {
                "email": "jane@example.com",
                "password": "wrongpassword123",
            }

            response = self.client.post(
                "/api/accounts/login/",
                login_data,
                format="json"
            )

            self.assertEqual(
                response.status_code,
                status.HTTP_400_BAD_REQUEST
            )

class LogoutTestCase(TestCase):
    def test_user_can_logout(self):

        response = self.client.post(
                '/api/accounts/logout/',
                format = "json"
        )
        self.assertIn(
            "message", response.data
        )

        self.assertEqual(
            response.status_code, status.HTTP_200_OK
        )

        cookie = response.cookies.get('refresh_token')
        
        if cookie:
            self.assertTrue(cookie.value == '')



class RefreshTokenTestCase(TestCase):

    def setUp(self):
        # Create user
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

        # Login user
        login_data = {
            "email": "jane@example.com",
            "password": "securepassword123",
        }

        response = self.client.post(
            "/api/accounts/login/",
            login_data,
            format="json"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )

        # Make sure login created refresh cookie
        self.assertIn(
            "refresh_token",
            response.cookies
        )


    def test_user_can_refresh(self):

        response = self.client.post(
            "/api/accounts/refresh/",
            format="json"
        )

        print("REFRESH RESPONSE:", response.data)
        print("REFRESH RESPONSE COOKIES:", response.cookies)

        # 1. Refresh request succeeded
        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED
        )

        # 2. Response contains message
        self.assertIn(
            "message",
            response.data
        )

        # 3. Message is exactly what we expect
        self.assertEqual(
            response.data["message"],
            "New Token Generated"
        )

        # 4. New refresh cookie should be returned
        cookie = response.cookies.get("refresh_token")

        self.assertIsNotNone(
            cookie
        )

        # 5. Cookie should contain a token
        self.assertTrue(
            len(cookie.value) > 0
        )


    def test_refresh_without_cookie(self):

        # Delete the refresh cookie created during setUp
        self.client.cookies.clear()

        response = self.client.post(
            "/api/accounts/refresh/",
            format="json"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED
        )

        self.assertIn(
            "error",
            response.data
        )

        self.assertEqual(
            response.data["error"],
            "Refresh token not found"
        )


    def test_refresh_with_invalid_token(self):

        # Replace the valid cookie with an invalid token
        self.client.cookies["refresh_token"] = "invalid-token"

        response = self.client.post(
            "/api/accounts/refresh/",
            format="json"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED
        )

        self.assertIn(
            "error",
            response.data
        )

        self.assertEqual(
            response.data["error"],
            "Invalid or expired refresh token"
        )



        