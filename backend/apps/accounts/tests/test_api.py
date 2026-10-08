
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

    def test_user_can_update_profile(self):
        access_token = self.login_response.data.get("access_token")
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {access_token}"
        )

        profile_data = {
            "first_name": "John",
            "last_name": "Doe",
            "phn_number": "9812345678",
        }

        response = self.client.patch(
            "/api/accounts/me/",
            profile_data,
            format="json"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )

        self.assertEqual(
            response.data["first_name"],
            "John"
        )

        self.assertEqual(
            response.data["last_name"],
            "Doe"
        )

        self.assertEqual(
            response.data["phn_number"],
            "9812345678"
        )

        self.user.refresh_from_db()

        self.assertEqual(
            self.user.first_name,
            "John"
        )

        self.assertEqual(
            self.user.last_name,
            "Doe"
        )

        self.assertEqual(
            self.user.phn_number,
            "9812345678"
        )

    def test_user_cannot_change_email_verification_status(self):
        access_token = self.login_response.data.get("access_token")
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {access_token}"
        )

        self.assertTrue(
            self.user.is_email_verified
        )

        profile_data = {
            "is_email_verified": True,
        }

        response = self.client.patch(
            "/api/accounts/me/",
            profile_data,
            format="json"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )

        self.user.refresh_from_db()

        self.assertFalse(
            self.user.is_email_verified
        )
    
class ChangePasswordTestCase(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            email="jane@example.com",
            password="securepassword123"
        )

        login_data = {
            "email": "jane@example.com",
            "password": "securepassword123",
        }

        self.login_response = self.client.post(
            "/api/accounts/login/",
            login_data,
            format="json"
        )

        self.assertEqual(
            self.login_response.status_code,
            status.HTTP_200_OK
        )

        self.access_token = self.login_response.data["access_token"]

    def test_password_can_be_changed(self):

        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {self.access_token}"
        )

        password_data = {
            "current_password": "securepassword123",
            "new_password": "newsecurepassword123",
        }

        response = self.client.post(
            "/api/accounts/change-password/",
            password_data,
            format="json"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )

        self.user.refresh_from_db()

        self.assertTrue(
            self.user.check_password(
                "newsecurepassword123"
            )
        )

        self.assertFalse(
            self.user.check_password(
                "securepassword123"
            )
        )
    
    def test_password_change_increments_token_version(self):

        self.assertEqual(
            self.user.token_version,
            0
        )

        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {self.access_token}"
        )

        password_data = {
            "current_password": "securepassword123",
            "new_password": "newsecurepassword123",
           
        }

        response = self.client.post(
            "/api/accounts/change-password/",
            password_data,
            format="json"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )

        self.user.refresh_from_db()

        self.assertEqual(
            self.user.token_version,
            1
        )

    def test_old_access_token_is_invalid_after_password_change(self):

        old_access_token = self.access_token

        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {old_access_token}"
        )

        password_data = {
            "current_password": "securepassword123",
            "new_password": "newsecurepassword123",
           
        }

        response = self.client.post(
            "/api/accounts/change-password/",
            password_data,
            format="json"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )

        # Try using the old access token
        response = self.client.get(
            "/api/accounts/me/"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED
        )


    def test_password_change_revokes_refresh_session(self):

        refresh_token = self.client.cookies["refresh_token"].value

        token = RefreshToken(refresh_token)

        session = RefreshSession.objects.get(
            token_jti=str(token["jti"])
        )

        self.assertIsNone(
            session.revoked_at
        )

        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {self.access_token}"
        )

        password_data = {
            "current_password": "securepassword123",
            "new_password": "newsecurepassword123",
          
        }

        response = self.client.post(
            "/api/accounts/change-password/",
            password_data,
            format="json"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )

        session.refresh_from_db()

        self.assertIsNotNone(
            session.revoked_at
        )

    def test_old_refresh_token_is_invalid_after_password_change(self):

        old_refresh_token = self.client.cookies["refresh_token"].value

        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {self.access_token}"
        )

        password_data = {
            "current_password": "securepassword123",
            "new_password": "newsecurepassword123",
            
        }

        response = self.client.post(
            "/api/accounts/change-password/",
            password_data,
            format="json"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )

        # Put the old refresh token back into the cookie
        self.client.cookies["refresh_token"] = old_refresh_token

        response = self.client.post(
            "/api/accounts/refresh/",
            format="json"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED
        )

    def test_password_change_fails_with_wrong_current_password(self):

        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {self.access_token}"
        )

        password_data = {
            "current_password": "wrongpassword123",
            "new_password": "newsecurepassword123",
        }

        response = self.client.post(
            "/api/accounts/change-password/",
            password_data,
            format="json"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST
        )



        

        