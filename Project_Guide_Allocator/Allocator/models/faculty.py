from django.db import models
from .myuser import MyUser

from Allocator.manager.faculty_manager import FacultyManager

class Faculty(models.Model):
    user = models.OneToOneField(MyUser, on_delete=models.CASCADE, primary_key=True)
    abbreviation = models.CharField(max_length=10, unique=True)

    objects=FacultyManager()

    def __str__(self):
        return self.abbreviation
