from django.db import models
from django.utils import timezone
from .myuser import MyUser
from .allocation_event import AllocationEvent  # Import AllocationEvent model

class Logs(models.Model):
    user = models.ForeignKey(MyUser, on_delete=models.CASCADE, primary_key=True, null=False, blank=False, related_name="student")
    event = models.ForeignKey(AllocationEvent, on_delete=models.SET_NULL, null=True, blank=True, related_name="logs")
    datetime = models.DateTimeField(default=timezone.now)
    action = models.CharField(max_length=25)

    def __str__(self):
        return f'{self.user.username} - {self.event} - {self.datetime}'
