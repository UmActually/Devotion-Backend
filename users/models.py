from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager


class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("The email field must be set")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save()
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields["is_superuser"] = True
        extra_fields["is_staff"] = True
        extra_fields["is_organization"] = False

        extra_fields.setdefault("name", "Alan")
        extra_fields.setdefault("last_name", "Turing")

        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    email = models.EmailField(unique=True, null=False)
    is_staff = models.BooleanField(default=False, null=False)
    name = models.CharField(max_length=64, null=False)
    last_name = models.CharField(max_length=64, null=True)

    objects = UserManager()

    def __str__(self):
        return self.email
