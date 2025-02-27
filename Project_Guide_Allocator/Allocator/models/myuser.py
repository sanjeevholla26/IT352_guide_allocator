from django.contrib.auth.models import AbstractUser
from django.db import models

from django.contrib.auth.models import BaseUserManager

class CustomUserManager(BaseUserManager):
    def create_user(self, edu_email, email, mobile_number, username, password=None, **extra_fields):
        if not edu_email:
            raise ValueError('The edu_email field must be set')
        if not edu_email.endswith("@nitk.edu.in"):
            raise ValueError('The Email ID must be an NITK edu mail ID.')
        edu_email = self.normalize_email(edu_email)
        user = self.model(username=username.strip(), email=email, edu_email=edu_email, mobile_number=mobile_number, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, edu_email, mobile_number, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        
        username="Admin"

        created_user = self.create_user(edu_email, "default@gmail.com", mobile_number, username, password,**extra_fields)
        created_user.is_registered = True
        created_user.save()
        
        return created_user


class MyUser(AbstractUser):
    # email = models.EmailField(unique=True)  # Override the default email field to make it unique
    edu_email = models.EmailField(unique=True)
    mobile_number = models.CharField(max_length=15, null=False)
    otp = models.CharField(max_length=10, blank=True, null=True)
    is_registered = models.BooleanField(default=False)
    failed_attempts = models.IntegerField(default=0)
    failed_blocked = models.DateTimeField(default=None, blank=True, null=True)

    def __str__(self):
        return self.edu_email

    objects = CustomUserManager()

    USERNAME_FIELD = 'edu_email'
    REQUIRED_FIELDS = ['username', 'mobile_number']

    def has_permission(self, fun, app):
        roles = self.roles.all()
        all_actions = {}

        for role in roles:
            for perm in role.permissions.all():
                app_name = perm.app_name
                actions = perm.actions.split(',')

                if app_name in all_actions:
                    all_actions[app_name].extend(actions)
                else:
                    all_actions[app_name] = actions

        for app_name in all_actions:
            all_actions[app_name] = list(set(all_actions[app_name]))
        if not app in all_actions or not fun in all_actions[app] :
            return False

        return True