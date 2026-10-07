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
    
    token_version = models.PositiveIntegerField(default=0)

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_email_verified = models.BooleanField(default=True)

    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now = True)

    #Connect User to Organization
    organizations = models.ManyToManyField(
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



class RefreshSession(models.Model):
        user = models.ForeignKey(
            User,
            on_delete=models.CASCADE,
            related_name="refresh_sessions"
        )

        token_jti = models.CharField(
             max_length=255,
             unique= True
        )

        created_at = models.DateTimeField(
             auto_now_add=True
        )

        expires_at = models.DateTimeField()

        revoked_at = models.DateTimeField(
             null= True,
             blank= True
        )

        last_used_at = models.DateTimeField(
             null= True,
             blank= True
        )