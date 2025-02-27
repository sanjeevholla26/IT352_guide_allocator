import re
from django.db import IntegrityError
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.shortcuts import render, redirect
from django.urls import reverse
from ..decorators import authorize_resource
from ..models import MyUser, Student, Role

import logging

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
            user = MyUser.objects.create_user(edu_email=edu_email, email=email, mobile_number=mobile_number, username=username, first_name = fname, last_name = lname)
            user.save()
        except IntegrityError as e:
            messages.error(request, "Roll number already exists.")
            return HttpResponseRedirect(reverse('add_student'))
        
        # Retrieve CGPA from the form and check if it's within the allowed range
        cgpa = float(request.POST["cgpa"])
        if cgpa < 0.0 or cgpa > 10.0:
            messages.error(request, "CGPA must be between 0.0 and 10.0.")
            return HttpResponseRedirect(reverse('add_student'))
            
        # Retrieve academic year from the form and check if it's a 4-digit number
        academic_year = request.POST["aca_year"]
        if not academic_year.isdigit() or len(academic_year) != 4:
            messages.error(request, "Academic year must be a 4-digit number.")
            return HttpResponseRedirect(reverse('add_student'))

        # Retrieve branch from the form and check if it matches "AI" or "IT"
        branch = request.POST["branch"]
        if branch not in ["AI", "IT"]:
            messages.error(request, "Branch must be either 'AI' or 'IT'.")
            return HttpResponseRedirect(reverse('add_student'))
        
        has_backlog = request.POST.get("has_backlog") == 'true'
        new_student = Student(
            user = user,
            cgpa = cgpa,
            academic_year = academic_year,
            branch = branch,
            has_backlog = has_backlog
        )
        new_student.save()

        # Student.objects.create_student(user=user, cgpa=cgpa, academic_year=academic_year, branch=branch)
        logger.info(f"User: {user.username} added as Student")

        student_role, created = Role.objects.get_or_create(role_name="student")
        student_role.users.add(user)
        student_role.save()

        return HttpResponseRedirect(reverse('home'))

    else:
        new_student = MyUser.objects.exclude(student__isnull=False).exclude(faculty__isnull=False)
        return render(request, "Allocator/add_student.html", {
            "users": new_student
        })