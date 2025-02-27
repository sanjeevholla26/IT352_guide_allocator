from django.db import models
from .allocation_event import AllocationEvent
from .faculty import Faculty
from .student import Student
from django.utils.timezone import now

from Allocator.manager.clash_manager import ClashesManager

class Clashes(models.Model):
    event = models.ForeignKey(AllocationEvent, on_delete=models.CASCADE)
    cluster_id = models.IntegerField()
    faculty = models.ForeignKey(Faculty, on_delete=models.CASCADE)
    preference_id = models.IntegerField()
    list_of_students = models.ManyToManyField('Student', related_name='clashing_students')  # A many-to-many relationship with the Student model
    selected_student = models.ForeignKey(Student, null=True, blank=True, on_delete=models.SET_NULL)
    created_datetime = models.DateTimeField(default=now)
    is_processed = models.BooleanField(default=False)

    objects=ClashesManager()

    def __str__(self):
        return f'Clash in {self.event.event_name} - Cluster {self.cluster_id}'
