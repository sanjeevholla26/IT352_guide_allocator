from django.db import models

class AllocationEventManager(models.Manager):
    def create_event(self, user, name, project_type, start_datetime, end_datetime, batch, branch, faculties):
        # Create the event instance first
        event = self.create(
            owner=user,  # Set the owner to the current user
            event_name=name,
            project_type=project_type,
            start_datetime=start_datetime,
            end_datetime=end_datetime,
            eligible_batch=batch,
            eligible_branch=branch
        )

        # Add eligible faculties after creating the event
        event.eligible_faculties.set(faculties)
        event.save()

        return event

    def update_event(self, event, name=None, status=None, project_type=None, start_datetime=None, end_datetime=None, batch=None, branch=None, faculties=None,cluster_count=None):
        """
        Update fields for an existing event instance. If any parameter is None, that field will not be updated.
        """
        # Update only if values are not None
        if name is not None:
            event.event_name = name
        if project_type is not None:
            event.project_type = project_type
        #TBD - Cascading for previous project-type choicelists, backlogs and clashes
        if start_datetime is not None:
            event.start_datetime = start_datetime
        if end_datetime is not None:
            event.end_datetime = end_datetime
        if batch is not None:
            event.eligible_batch = batch
        if branch is not None:
            event.eligible_branch = branch
        if cluster_count is not None:
            event.cluster_count = cluster_count
        
        # Faculties need to be set separately if not None
        if faculties is not None:
            event.eligible_faculties.set(faculties)

        # event.status = 'open'

        # Save changes
        event.save()

        return event

