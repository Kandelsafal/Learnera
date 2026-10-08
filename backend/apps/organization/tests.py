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
        Membership.objects.create(
            user=self.user,
            organization=self.org,
            role=Membership.Role.Learner
        )

        self.assertIn(self.user, self.org.users.all())
        self.assertIn(self.org, self.user.organizations.all())
        self.assertEqual(self.user.memberships.get().role, "LEARNER")

    def test_unique_membership_constraint(self):
        Membership.objects.create(
            user=self.user,
            organization=self.org,
            role=Membership.Role.Learner
        )

        with self.assertRaises(Exception):
            Membership.objects.create(
                user=self.user,
                organization=self.org,
                role=Membership.Role.Instructor
            )

    def test_relationships(self):
        Membership.objects.create(
            user=self.user,
            organization=self.org,
            role=Membership.Role.Learner
        )

        self.assertEqual(self.org.users.count(), 1)
        self.assertEqual(self.user.organizations.count(), 1)
        self.assertEqual(self.user.memberships.count(), 1)
        self.assertEqual(self.org.memberships.count(), 1)   


    def test_membership_deleted_when_user_deleted(self):
        Membership.objects.create(
            user=self.user,
            organization=self.org,
            role=Membership.Role.Learner
        )

        self.user.delete()

        self.assertEqual(
            Membership.objects.filter(
                organization=self.org
            ).count(),
            0
        )