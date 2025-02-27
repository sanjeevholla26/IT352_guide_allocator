from django.db import IntegrityError, transaction
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.shortcuts import render, redirect
from django.urls import reverse
from ..decorators import authorize_resource
from ..models import MyUser, Student, Role

import logging
import re

logger = logging.getLogger('django')

@authorize_resource
def add_student(request):
    if request.method == "POST":
        username = request.POST["username"]
        edu_email = request.POST["edu_mail"]

        if not edu_email.endswith("@nitk.edu.in"):
            messages.error(request, "The Email ID must be an NITK edu mail ID.")
            return HttpResponseRedirect(reverse('add_student'))
        
        email = request.POST["email"]
        fname = request.POST["fname"]
        lname = request.POST["lname"]
        mobile_number = request.POST.get("mobile_number")

        if not re.fullmatch(r'^\d{10}$', mobile_number):
            messages.error(request, "Mobile number must be exactly 10 digits.")
            return HttpResponseRedirect(reverse('add_student'))

        try:
            with transaction.atomic():  # Ensures atomicity
                user = MyUser.objects.create_user(
                    edu_email=edu_email, email=email, mobile_number=mobile_number,
                    username=username, first_name=fname, last_name=lname
                )
                user.save()

                cgpa = float(request.POST["cgpa"])
                if cgpa < 0.0 or cgpa > 10.0:
                    messages.error(request, "CGPA must be between 0.0 and 10.0.")
                    user.delete()  # Delete user if validation fails
                    return HttpResponseRedirect(reverse('add_student'))

                academic_year = request.POST["aca_year"]
                if not academic_year.isdigit() or len(academic_year) != 4:
                    messages.error(request, "Academic year must be a 4-digit number.")
                    user.delete()
                    return HttpResponseRedirect(reverse('add_student'))

                branch = request.POST["branch"]
                if branch not in ["AI", "IT"]:
                    messages.error(request, "Branch must be either 'AI' or 'IT'.")
                    user.delete()
                    return HttpResponseRedirect(reverse('add_student'))

                has_backlog = request.POST.get("has_backlog") == 'true'
                course_type = request.POST["course_type"]
                has_internship = request.POST.get("has_internship") == 'true' if course_type == "M.Tech" else None

                new_student = Student(
                    user=user,
                    cgpa=cgpa,
                    academic_year=academic_year,
                    branch=branch,
                    has_backlog=has_backlog,
                    course_type=course_type,
                    has_internship=has_internship
                )
                new_student.save()

                student_role, created = Role.objects.get_or_create(role_name="student")
                student_role.users.add(user)
                student_role.save()

        except IntegrityError:
            messages.error(request, "Roll number already exists.")
            return HttpResponseRedirect(reverse('add_student'))

        except Exception as e:
            logger.error(f"Error creating student: {e}")
            messages.error(request, "An error occurred while creating the student.")
            user.delete()
            return HttpResponseRedirect(reverse('add_student'))

        return HttpResponseRedirect(reverse('home'))

    else:
        new_student = MyUser.objects.exclude(student__isnull=False).exclude(faculty__isnull=False)
        return render(request, "Allocator/add_student.html", {"users": new_student})
