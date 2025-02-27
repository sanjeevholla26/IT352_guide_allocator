from django.db import models

class ChoiceListManager(models.Manager):
    def create_choice_list(self, event, student, preference_list, cluster_number):
        # Create the ChoiceList object
        choice_list = self.create(
            event=event,
            student=student,
            preference_list=preference_list,
            cluster_number=cluster_number,
            current_index=1,
            is_locked=False
        )
        return choice_list

    def update_choice_list(self, choice_list, preference_list=None, current_allocation=None, current_index=None, cluster_number=None, is_locked=None):
        # Update fields if new values are provided
        if preference_list is not None:
            choice_list.preference_list = preference_list
        if current_allocation is not None:
            choice_list.current_allocation = current_allocation
        if current_index is not None:
            choice_list.current_index = current_index
        if cluster_number is not None:
            choice_list.cluster_number = cluster_number
        if is_locked is not None:
            choice_list.is_locked = is_locked
        
        # Save changes
        choice_list.save()
        return choice_list

    def get_choices_by_event(self, event):
        # Retrieve all choice lists for a specific event
        return self.filter(event=event)

    def get_locked_choices(self):
        # Retrieve all locked choice lists
        return self.filter(is_locked=True)

    def get_unallocated_choices(self):
        # Retrieve choice lists that haven't been allocated yet (current_allocation is None)
        return self.filter(current_allocation__isnull=True)
