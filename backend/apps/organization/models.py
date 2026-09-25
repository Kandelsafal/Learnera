from django.db import models

# Create your models here.
from django.db import models
from django.utils import timezone

#Organization Model with Unique Slug
class Organization(models.Model):
    name = models.CharField(
        unique= True,
        max_length=240)

    slug = models.SlugField(unique= True)
    created_at = models.DateTimeField(default = timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

#Membership Model for every Organization
class Membership(models.Model):

    class Role (models.TextChoices):
        Learner = "LEARNER", "Learner",
        Instructor = "INSTRUCTOR", "Instructor",
        Manager = "MANAGER", "Manager",
        ADMIN = "ADMIN", "Admin"

    #User
    user = models.ForeignKey("accounts.User", on_delete=models.CASCADE, related_name="memberships")
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="memberships")
    role = models.CharField(max_length=20 ,choices=Role.choices, default= Role.Learner)
    joined_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now= True)

    #Data Container (Configuration of the Model)
    class Meta:
        unique_together = ("user", "organization")

    def __str__(self):
        return f"{self.user} ->{self.organization} - {self.role} "