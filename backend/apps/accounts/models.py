from django.utils import timezone

from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from .manager import UserManager


# Create your models here.

class User(AbstractBaseUser, PermissionsMixin):
    first_name = models.CharField(
        max_length=100,
    
    )

    last_name = models.CharField(
        max_length=140
    )

    email = models.EmailField(
        unique= True
    )

    phn_number = models.CharField(
        unique= True,
        null=True,
        blank=True,
        max_length= 15
    )

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_email_verified = models.BooleanField(default=False)

    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now = True)

    #Connect User to Organization
    organization = models.ManyToManyField(
        "organization.Organization",
        through="organization.Membership",
        related_name="users",
        blank=True )

    #Use email as the user name 
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["first_name","last_name"]

    #Connect Manager to Model
    objects = UserManager()

    #Return User object with email 
    def __str__(self):
         #Return String   
        return f"{self.first_name} {self.last_name} ({self.email})"