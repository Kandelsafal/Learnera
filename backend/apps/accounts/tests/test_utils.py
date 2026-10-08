from django.test import TestCase

from apps.accounts.utils import generate_email_verification_token
from django.test import SimpleTestCase
from django.contrib.auth import get_user_model
from apps.accounts.utils import generate_email_verification_token
from rest_framework import status
from datetime import timedelta

from django.utils import timezone

from apps.accounts.models import EmailVerificationToken

User = get_user_model()

class EmailVerificationTokenTestCase(TestCase):

    def test_token_generation(self):

        raw_token, token_hash = generate_email_verification_token()

        self.assertIsNotNone(raw_token)
        self.assertIsNotNone(token_hash)

        self.assertNotEqual(
            raw_token,
            token_hash
        )

        self.assertEqual(
            len(token_hash),
            64
        )

    def test_registration_creates_email_verification_token(self):

        response = self.client.post(
            "/api/accounts/register/",
            {
                "email": "verify@example.com",
                "first_name": "Verify",
                "last_name": "User",
                "password": "SecurePassword123!",
                "phn_number": "9812345678",
            },
            format="json"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED
        )

        user = User.objects.get(
            email="verify@example.com"
        )

        self.assertFalse(
            user.is_email_verified
        )

        verification_token = EmailVerificationToken.objects.get(
            user=user
        )

        self.assertIsNotNone(
            verification_token.token_hash
        )

        self.assertIsNotNone(
            verification_token.expires_at
        )

        self.assertIsNone(
            verification_token.used_at
        )

    def test_user_can_verify_email(self):

        user = User.objects.create_user(
            email="verify@example.com",
            password="SecurePassword123!"
        )

        raw_token, token_hash = generate_email_verification_token()

        EmailVerificationToken.objects.create(
            user=user,
            token_hash=token_hash,
            expires_at=timezone.now() + timedelta(minutes=15)
        )

        self.assertFalse(
            user.is_email_verified
        )

        response = self.client.post(
            "/api/accounts/verify-email/",
            {
                "token": raw_token
            },
            format="json"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )

        user.refresh_from_db()

        self.assertTrue(
            user.is_email_verified
        )

        verification_token = EmailVerificationToken.objects.get(
            token_hash=token_hash
        )

        self.assertIsNotNone(
            verification_token.used_at
        )

    def test_used_token_cannot_be_used_again(self):

        user = User.objects.create_user(
            email="verify@example.com",
            password="SecurePassword123!"
        )

        raw_token, token_hash = generate_email_verification_token()

        EmailVerificationToken.objects.create(
            user=user,
            token_hash=token_hash,
            expires_at=timezone.now() + timedelta(minutes=15),
            used_at=timezone.now()
        )

        response = self.client.post(
            "/api/accounts/verify-email/",
            {
                "token": raw_token
            },
            format="json"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST
        )

    def test_expired_token_cannot_be_used(self):

        user = User.objects.create_user(
            email="expired@example.com",
            password="SecurePassword123!"
        )

        raw_token, token_hash = generate_email_verification_token()

        EmailVerificationToken.objects.create(
            user=user,
            token_hash=token_hash,
            expires_at=timezone.now() - timedelta(minutes=1)
        )

        response = self.client.post(
            "/api/accounts/verify-email/",
            {
                "token": raw_token
            },
            format="json"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST
        )

        user.refresh_from_db()

        self.assertFalse(
            user.is_email_verified
        )

    def test_invalid_token_cannot_be_used(self):

        user = User.objects.create_user(
            email="invalid@example.com",
            password="SecurePassword123!"
        )

        response = self.client.post(
            "/api/accounts/verify-email/",
            {
                "token": "this-is-not-a-real-verification-token"
            },
            format="json"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST
        )

        user.refresh_from_db()

        self.assertFalse(
            user.is_email_verified
        )