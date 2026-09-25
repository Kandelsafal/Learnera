from django.test import TestCase
from apps.accounts.models import User
class UserTestCase(TestCase):
    
    def setUp(self):
        self.user = User.objects.create(
            email="student@example.com", 
            first_name="John", 
            last_name="Doe"
        )
        self.user.set_password("securepassword123")
        self.user.save()

    def test_user_creation_and_password(self):
        """Test that the user is created properly and password hashing works."""
        # Check basic fields
        self.assertEqual(self.user.email, "student@example.com")
        self.assertEqual(self.user.first_name, "John")
        self.assertTrue(self.user.is_active)
        
        # Check that string representation matches your __str__ method
        self.assertEqual(str(self.user), "John Doe (student@example.com)")
        
        # Check that password hashing works
        self.assertTrue(self.user.check_password("securepassword123"))
        self.assertFalse(self.user.check_password("wrongpassword"))