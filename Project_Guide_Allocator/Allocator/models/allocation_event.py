from django.db import models
from django.utils import timezone
from enum import Enum
from .myuser import MyUser
from .faculty import Faculty
from Allocator.manager.allocation_event_manager import AllocationEventManager
from .student import Student

class event_status(Enum):
    OPEN = 'open'
    LOCKED = 'locked'
    CLOSED = 'closed'

    @classmethod
    def choices(cls):
        return [(key.value, key.name.capitalize()) for key in cls]

class project_type(Enum):
    BTECH = 'B.Tech'
    MTECHMAJ = 'M.Tech Major'
    MTECHMIN = 'M.Tech Minor'

    @classmethod
    def choices(cls):
        return [(key.value, key.name.capitalize()) for key in cls]
    
class AllocationEvent(models.Model):
    event_name = models.CharField(max_length=255)
    status = models.CharField(max_length=6, choices=event_status.choices(), default='open')
    project_type = models.CharField(max_length=14, choices=project_type.choices(), default='B.Tech')
    owner = models.ForeignKey(MyUser, on_delete=models.CASCADE)
    start_datetime = models.DateTimeField()
    end_datetime = models.DateTimeField()
    eligible_batch = models.CharField(max_length=255)  # e.g., "2026"
    eligible_branch = models.CharField(max_length=255)  # e.g., "IT,AI"
    eligible_faculties = models.ManyToManyField(Faculty, related_name='eligible_faculty_events')
    cluster_count = models.IntegerField(default=0)
    for_backlog=models.BooleanField(default=False)
    eligible_students = models.ManyToManyField(Student, related_name='eligible_events', blank=True)

    objects=AllocationEventManager()

    def __str__(self):
        return self.event_name

    @classmethod
    def active_events(cls):
        """Return all events that are currently active."""
        now = timezone.now()
        return cls.objects.filter(start_datetime__lte=now, end_datetime__gte=now)
