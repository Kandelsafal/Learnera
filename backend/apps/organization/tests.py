from django.test import TestCase
from apps.accounts.models import User
from apps.organization.models import Organization, Membership

class OrganizationMembershipTestCase(TestCase):
    
    def setUp(self):
        self.org = Organization.objects.create(
            name="Tech University", 
            slug="tech-university"
        )
        
        self.user = User.objects.create(
            email="student@example.com", 
            first_name="John", 
            last_name="Doe"
        )
        self.user.set_password("securepassword123")
        self.user.save()

    # --- ADD YOUR TEST METHODS HERE ---
    def test_membership_and_lookups(self):
        membership = Membership.objects.create(
            user=self.user,
            organization=self.org,
            role=Membership.Role.LEARNER
        )

        self.assertIn(self.user, self.org.users.all())
        self.assertIn(self.org, self.user.organizations.all())
        self.assertEqual(self.user.memberships.get().role, "LEARNER")

    def test_unique_membership_constraint(self):
        Membership.objects.create(
            user=self.user,
            organization=self.org,
            role=Membership.Role.LEARNER
        )

        with self.assertRaises(Exception):
            Membership.objects.create(
                user=self.user,
                organization=self.org,
                role=Membership.Role.INSTRUCTOR
            )