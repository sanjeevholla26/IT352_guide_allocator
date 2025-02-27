from django.db import models

class StudentManager(models.Manager):
    def create_student(self, user, cgpa, academic_year, branch):
        """
        Creates a new student instance.
        """
        if not user or cgpa is None or academic_year is None or not branch:
            raise ValueError("All fields (user, cgpa, academic year, and branch) are required.")


        student = self.create(
            user=user,
            cgpa=cgpa,
            academic_year=academic_year,
            branch=branch
        )

        return student

    def update_student(self, user, cgpa=None, academic_year=None, branch=None):
        """
        Updates an existing student's information. Fields can be updated selectively.
        """
        try:
            student = self.get(user=user)
        except self.model.DoesNotExist:
            raise ValueError(f"No student found with user {user}")

        # Update fields if provided
        if cgpa is not None:
            student.cgpa = cgpa

        if academic_year is not None:
            student.academic_year = academic_year

        if branch is not None:
            student.branch = branch

        student.save()
        return student

    def get_students_by_branch(self, branch):
        """
        Retrieves all students in a specific branch.
        """
        return self.filter(branch=branch)

    def get_students_by_academic_year(self, year):
        """
        Retrieves all students by academic year.
        """
        return self.filter(academic_year=year)

