from django.db import models
from .role import Role

class Permission(models.Model):
    role = models.ManyToManyField(Role, blank=True, related_name='permissions')
    actions = models.CharField(max_length=1000)  # List of actions as a comma-separated string
    app_name = models.CharField(max_length=100)  # Application name
