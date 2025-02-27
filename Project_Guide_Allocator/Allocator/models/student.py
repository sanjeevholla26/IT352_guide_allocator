from django.db import models
from .myuser import MyUser
from enum import Enum

from Allocator.manager.student_manager import StudentManager

class course_type(Enum):
    BTECH = 'B.Tech'
    MTECH = 'M.Tech'

    @classmethod
    def choices(cls):
        return [(key.value, key.name.capitalize()) for key in cls]
    
class Student(models.Model):
    user = models.OneToOneField(MyUser, on_delete=models.CASCADE, primary_key=True, related_name="student")
    cgpa = models.DecimalField(max_digits=4, decimal_places=2)
    academic_year = models.IntegerField()  # e.g., 2024
    branch = models.CharField(max_length=100)
    has_backlog = models.BooleanField(default=False)
    has_internship = models.BooleanField(default=False)
    course_type = models.CharField(max_length=14, choices=course_type.choices(), default='B.Tech')
    # mobile_number = models.CharField(max_length=15, blank=True)

    objects=StudentManager()

    def __str__(self):
        return f'{self.user.username} - {self.branch}'

