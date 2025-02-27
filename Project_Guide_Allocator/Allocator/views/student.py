import csv
import io
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
        csv_file = request.FILES.get("csv_file")

        if csv_file:
            # Validate file extension
            if not csv_file.name.endswith('.csv'):
                messages.error(request, "File must be a CSV.")
                return redirect("add_student")

            # Read and process the CSV file
            data = csv_file.read().decode("utf-8")
            csv_reader = csv.reader(io.StringIO(data))
            next(csv_reader)  # Skip header

            added_students = 0
            for row in csv_reader:
                if len(row) < 9:
                    messages.error(request, "CSV format is incorrect. Each row must have 9 fields.")
                    return redirect("add_student")

                username, edu_email, email, fname, lname, mobile_number, cgpa, branch, academic_year, has_backlog = row

                # Validate email
                if not edu_email.endswith("@nitk.edu.in"):
                    messages.error(request, f"{edu_email} is not a valid NITK edu mail ID.")
                    continue

                # Validate mobile number
                if not re.fullmatch(r'^\d{10}$', mobile_number):
                    messages.error(request, f"Mobile number {mobile_number} must be exactly 10 digits.")
                    continue

                # Validate CGPA
                try:
                    cgpa = float(cgpa)
                    if cgpa < 0.0 or cgpa > 10.0:
                        messages.error(request, f"CGPA {cgpa} must be between 0.0 and 10.0.")
                        continue
                except ValueError:
                    messages.error(request, f"CGPA {cgpa} is not a valid number.")
                    continue

                # Validate academic year
                if not academic_year.isdigit() or len(academic_year) != 4:
                    messages.error(request, f"Academic year {academic_year} must be a 4-digit number.")
                    continue

                # Validate branch
                if branch not in ["AI", "IT"]:
                    messages.error(request, f"Branch {branch} must be either 'AI' or 'IT'.")
                    continue

                # Convert backlog field
                has_backlog = has_backlog.strip().lower() == "true"

                try:
                    user = MyUser.objects.create_user(
                        edu_email=edu_email.strip(),
                        email=email.strip(),
                        mobile_number=mobile_number.strip(),
                        username=username.strip(),
                        first_name=fname.strip(),
                        last_name=lname.strip()
                    )
                    user.save()

                    new_student = Student(
                        user=user,
                        cgpa=cgpa,
                        academic_year=academic_year,
                        branch=branch,
                        has_backlog=has_backlog
                    )
                    new_student.save()

                    # Assign the student role
                    student_role, _ = Role.objects.get_or_create(role_name="student")
                    student_role.users.add(user)
                    student_role.save()

                    logger.info(f"User: {user.username} added as Student")
                    added_students += 1

                except IntegrityError:
                    messages.error(request, f"Roll number {username} already exists.")
                    continue

            messages.success(request, f"{added_students} students added successfully!")
            return redirect("add_student")

        # Handle manual form submission (existing logic)
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
            user = MyUser.objects.create_user(
                edu_email=edu_email,
                email=email,
                mobile_number=mobile_number,
                username=username,
                first_name=fname,
                last_name=lname
            )
            user.save()
        except IntegrityError:
            messages.error(request, "Roll number already exists.")
            return HttpResponseRedirect(reverse('add_student'))

        # Validate CGPA
        cgpa = float(request.POST["cgpa"])
        if cgpa < 0.0 or cgpa > 10.0:
            messages.error(request, "CGPA must be between 0.0 and 10.0.")
            return HttpResponseRedirect(reverse('add_student'))

        # Validate Academic Year
        academic_year = request.POST["aca_year"]
        if not academic_year.isdigit() or len(academic_year) != 4:
            messages.error(request, "Academic year must be a 4-digit number.")
            return HttpResponseRedirect(reverse('add_student'))

        # Validate Branch
        branch = request.POST["branch"]
        if branch not in ["AI", "IT"]:
            messages.error(request, "Branch must be either 'AI' or 'IT'.")
            return HttpResponseRedirect(reverse('add_student'))

        has_backlog = request.POST.get("has_backlog") == 'true'
        new_student = Student(
            user=user,
            cgpa=cgpa,
            academic_year=academic_year,
            branch=branch,
            has_backlog=has_backlog
        )
        new_student.save()

        logger.info(f"User: {user.username} added as Student")

        student_role, _ = Role.objects.get_or_create(role_name="student")
        student_role.users.add(user)
        student_role.save()

        return HttpResponseRedirect(reverse('home'))

    else:
        new_student = MyUser.objects.exclude(student__isnull=False).exclude(faculty__isnull=False)
        return render(request, "Allocator/add_student.html", {
            "users": new_student
        })
