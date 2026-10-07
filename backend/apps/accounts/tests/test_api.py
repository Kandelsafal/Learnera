
from django.test import TestCase
from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model
from apps.accounts.models import RefreshSession
from rest_framework_simplejwt.tokens import RefreshToken
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

    def test_user_login_with_refreshSession(self):
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

        user_id = response.data["user"]["id"]

        session = RefreshSession.objects.get(
            user_id = user_id
        )

        # Get the refresh token from the cookie
        refresh_token = response.cookies["refresh_token"].value

        #Decode Token
        token = RefreshToken(refresh_token)

        # The JTI inside the JWT should match the database session
        self.assertEqual(
            session.token_jti,
            str(token["jti"])
        )

class LogoutTestCase(TestCase):
    def setUp(self):
        # 1. Create the user first so login actually works!
        self.user = User.objects.create_user(
            email="jane@example.com",
            password="securepassword123"
        )
        
        # 2. Log in to establish the cookie
        login_data = {
            "email": "jane@example.com",
            "password": "securepassword123",
        }
        
        response = self.client.post(
            "/api/accounts/login/",
            login_data,
            format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK) # Usually login returns 200 (adjust if yours returns 201)

    def test_user_can_logout(self):
        response = self.client.post(
            '/api/accounts/logout/',
            format="json"
        )
        self.assertIn("message", response.data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check that the cookie was cleared
        cookie = response.cookies.get('refresh_token')
        if cookie:
            self.assertEqual(cookie.value, '')

    def test_user_logout_session(self):
        # Extract the cookie value string
        cookie_morsel = self.client.cookies.get("refresh_token")
        self.assertIsNotNone(cookie_morsel)
        
        decode_token = RefreshToken(cookie_morsel.value)
        token_jti = decode_token["jti"]

        # Fetch the session object from DB
        current_session = RefreshSession.objects.get(
            token_jti=token_jti
        )

        # Perform logout
        response = self.client.post(
            '/api/accounts/logout/',
            format="json"
        )
        self.assertIn("message", response.data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Refresh the instance from the database to see the updated timestamps
        current_session.refresh_from_db()

        self.assertIsNotNone(current_session.revoked_at)
        self.assertIsNotNone(current_session.last_used_at)



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


    def test_refresh_rotates_token(self):
             
             old_refresh_token = self.client.cookies["refresh_token"].value
             old_token = RefreshToken(old_refresh_token)
             old_jti = str(old_token["jti"])

             response = self.client.post(
                        "/api/accounts/refresh/",
                        format="json"
                    )
    
             cookie = response.cookies["refresh_token"].value
             new_token = RefreshToken(cookie)
             new_jti = str(new_token["jti"])
             self.assertNotEqual(
                 new_jti, old_jti
             )
             #Find Old Session
             old_token = RefreshSession.objects.get(
                  token_jti = old_jti
             )
             #Old Session Must be Revoked
             self.assertIsNotNone(
                  old_token.revoked_at
             )

    def test_new_refresh_token_works_after_rotation(self):
        
        # First refresh
        first_refresh_response = self.client.post(
            "/api/accounts/refresh/"
        )

        self.assertEqual(
            first_refresh_response.status_code,
            201
        )

        # Client now has the NEW refresh token
        second_refresh_response = self.client.post(
            "/api/accounts/refresh/"
        )

        self.assertEqual(
            second_refresh_response.status_code,
            201
        )

        self.assertIn(
            "access_token",
            second_refresh_response.data
        )

    def test_old_refresh_token_cannot_be_reused(self):
        

        old_refresh_token = self.client.cookies["refresh_token"].value

        # First refresh
        first_refresh_response = self.client.post(
            "/api/accounts/refresh/"
        )

        self.assertEqual(
            first_refresh_response.status_code,
            201
        )

        # Put the OLD token back into the cookie
        self.client.cookies["refresh_token"] = old_refresh_token

        # Try to reuse old token
        second_refresh_response = self.client.post(
            "/api/accounts/refresh/"
        )

        self.assertEqual(
            second_refresh_response.status_code,
            401
        )

        self.assertEqual(
            second_refresh_response.data["error"],
            "Refresh session has been revoked"
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

class MeTestCase(APITestCase):
    def setUp(self):
        # 1. Create the user first so login actually works!
                self.user = User.objects.create_user(
                    email="jane@example.com",
                    password="securepassword123"
                )
                
                # 2. Log in to establish the cookie
                login_data = {
                    "email": "jane@example.com",
                    "password": "securepassword123",
                }
                
                self.login_response = self.client.post(
                    "/api/accounts/login/",
                    login_data,
                    format="json"
                )
        
                self.assertEqual(self.login_response.status_code, status.HTTP_200_OK)

    def test_me_with_access_token(self):
        access_token = self.login_response.data.get("access_token")
        
        # Attach the access token to the test client's header
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")
        
        # Hit the protected /me/ endpoint
        response = self.client.get("/api/accounts/me/", format="json")
        
        # Assertions
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get("email"), self.user.email)

    def test_me_without_access_token(self):
        response = self.client.get("/api/accounts/me/", format="json")
                 
                 # Assertions
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    



        