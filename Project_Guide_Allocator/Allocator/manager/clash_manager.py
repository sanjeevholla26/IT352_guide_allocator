from django.db import models
from django.utils.timezone import now

class ClashesManager(models.Manager):
    def create_clash(self, event, cluster_id, faculty, preference_id, list_of_students):
        """
        Create a new Clash instance with the provided details.
        """
        clash = self.create(
            event=event,
            cluster_id=cluster_id,
            faculty=faculty,
            preference_id=preference_id,
            created_datetime=now(),
            is_processed=False
        )
        # Add the students to the many-to-many relationship
        clash.list_of_students.set(list_of_students)
        return clash

    def update_clash(self, clash, selected_student=None, is_processed=None):
        """
        Update the details of an existing clash.
        """
        if selected_student is not None:
            clash.selected_student = selected_student
        if is_processed is not None:
            clash.is_processed = is_processed
        
        clash.save()
        return clash

    def get_unprocessed_clashes(self):
        """
        Retrieve all clashes that haven't been processed yet.
        """
        return self.filter(is_processed=False)

    def get_clashes_for_event(self, event):
        """
        Retrieve all clashes for a specific event.
        """
        return self.filter(event=event)

    def get_clashes_for_faculty(self, faculty):
        """
        Retrieve all clashes related to a specific faculty member.
        """
        return self.filter(faculty=faculty)
