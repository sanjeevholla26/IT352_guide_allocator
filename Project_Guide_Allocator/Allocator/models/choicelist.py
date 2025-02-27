from django.db import models
from .faculty import Faculty
from .student import Student
from .allocation_event import AllocationEvent

from Allocator.manager.choicelist_manager import ChoiceListManager

class ChoiceList(models.Model):
    event = models.ForeignKey(AllocationEvent, on_delete=models.CASCADE)
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    preference_list = models.JSONField()  # stores list of dictionaries e.g., [{"choiceNo": 1, "facultyID": "CS"}]
    current_allocation = models.ForeignKey(Faculty, null=True, blank=True, on_delete=models.SET_NULL, related_name='allocated_choices')
    current_index = models.IntegerField(default=1)
    cluster_number = models.IntegerField()
    is_locked = models.BooleanField(default=False)

    objects=ChoiceListManager()

    def __str__(self):
        return f'{self.student.user.username} - {self.event.event_name}'

    def allottedProf(self):
        if self.current_allocation:
            return self.current_allocation.abbreviation
        else:
            return ""

    def printRange(self, lower, higher):
        choiceList = ""
        for i in range(lower, higher):
            fac = Faculty.objects.get(user_id=int(self.preference_list[i]["facultyID"]))
            if i!=lower :
                choiceList = f"{choiceList},{fac.abbreviation}"
            else:
                choiceList = fac.abbreviation
        return choiceList

    def printChoiceList(self):
        return self.printRange(0, len(self.preference_list))

    def previousChoices(self):
        return self.printRange(0, self.current_index-1)

    def currentChoice(self):
        return Faculty.objects.get(user_id=int(self.preference_list[self.current_index-1]["facultyID"])).abbreviation

    def nextChoices(self):
        return self.printRange(self.current_index, len(self.preference_list))
