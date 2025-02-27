#Copy with the model to avoid circular dependency : Role->MyUser->Manger->Role

from django.contrib.auth.models import BaseUserManager
from Allocator.models.role import Role

class CustomUserManager(BaseUserManager):
    def create_user(self, edu_email, email, username, password=None, **extra_fields):
        """
        Creates and saves a User with the given edu_email, email, username, and password.
        """
        if not edu_email:
            raise ValueError('The edu_email field must be set')
        if not edu_email.endswith("@nitk.edu.in"):
            raise ValueError('The Email ID must be an NITK edu mail ID.')

        edu_email = self.normalize_email(edu_email)

        # Check if the username or edu_email already exists
        if self.model.objects.filter(edu_email=edu_email).exists():
            raise ValueError('A user with this edu_email already exists.')
        if self.model.objects.filter(username=username).exists():
            raise ValueError('A user with this username already exists.')

        # Create the user
        user = self.model(username=username.strip(), email=email, edu_email=edu_email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, edu_email, password=None, **extra_fields):
        """
        Creates and saves a SuperUser with the given username, edu_email, and password.
        """
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        # Create superuser and assign them the admin role
        created_user = self.create_user(edu_email, "default@gmail.com", username, password, **extra_fields)

        # Assign 'admin' role
        admin_role, created = Role.objects.get_or_create(role_name="admin")
        admin_role.users.add(created_user)
        admin_role.save()

        return created_user
