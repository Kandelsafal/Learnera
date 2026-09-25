from django.contrib.auth.models import AbstractBaseUser, BaseUserManager 



class UserManager(BaseUserManager):
   #Create Normal User 
    def create_user(self, email, password = None, **extra_fields):

        #Validation of Email
        if not email:
            raise ValueError("Email Required");

        email = self.normalize_email(email)

         #Create User in Model   
        user = self.model(
            email = email,
            **extra_fields
        )
        #Save Passowrd with Hashing
        user.set_password(password)
        user.save(using=self._db)
        return user

#Create Super User (Admin)
    def create_superuser(self, email, password= None, **extra_fields):

        extra_fields.setdefault("is_active", True)
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if extra_fields.get("is_active") is not True:
            raise ValueError("Superuser must have is_active=True.")
        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self.create_user(
            email,
            password,
            **extra_fields
        )

        