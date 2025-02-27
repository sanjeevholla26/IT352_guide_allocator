from django.db import models

class FacultyManager(models.Manager):
    def create_faculty(self, user, abbreviation):
        """
        Create a new faculty instance.
        """
        if not user or not abbreviation:
            raise ValueError("User and abbreviation are required fields.")

        # Create a new Faculty object and save it
        faculty = self.create(user=user, abbreviation=abbreviation)
        return faculty

    def get_by_abbreviation(self, abbreviation):
        """
        Retrieve a faculty member by their abbreviation.
        """
        try:
            return self.get(abbreviation=abbreviation)
        except self.model.DoesNotExist:
            return None

    def update_faculty(self, faculty, abbreviation=None):
        """
        Update the abbreviation of an existing faculty member.
        """
        if abbreviation is not None:
            faculty.abbreviation = abbreviation
            faculty.save()

        return faculty

    def delete_faculty(self, faculty):
        """
        Delete a faculty member from the database.
        """
        faculty.delete()
