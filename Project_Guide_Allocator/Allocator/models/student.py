from django.db import models
from .myuser import MyUser

from Allocator.manager.student_manager import StudentManager

class Student(models.Model):
    user = models.OneToOneField(MyUser, on_delete=models.CASCADE, primary_key=True, related_name="student")
    cgpa = models.DecimalField(max_digits=4, decimal_places=2)
    academic_year = models.IntegerField()  # e.g., 2024
    branch = models.CharField(max_length=100)
    has_backlog = models.BooleanField(default=False)
    # mobile_number = models.CharField(max_length=15, blank=True)

    objects=StudentManager()

    def __str__(self):
        return f'{self.user.username} - {self.branch}'

