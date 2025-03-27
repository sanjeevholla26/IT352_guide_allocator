import csv
import io
import re
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.shortcuts import render, redirect
from django.urls import reverse
from django.db import IntegrityError, transaction
from ..decorators import authorize_resource
from ..models import MyUser, Student, Role
import logging
import re

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

                username, edu_email, email, fname, lname, mobile_number, cgpa, branch, academic_year, has_backlog, course_type, has_internship = row

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

                has_backlog = has_backlog.strip().lower() == "true"

                try:
                    with transaction.atomic():
                        user = MyUser.objects.create_user(
                            edu_email=edu_email.strip(),
                            email=email.strip(),
                            mobile_number=mobile_number.strip(),
                            username=username.strip(),
                            first_name=fname.strip(),
                            last_name=lname.strip(),
                        )
                        user.save()
                        if not has_internship:
                            has_internship=False
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
                        student_role, _ = Role.objects.get_or_create(role_name="student")
                        student_role.users.add(user)
                        student_role.save()

                        logger.info(f"User: {user.username} added as Student")
                        added_students += 1

                except IntegrityError:
                    messages.error(request, f" {username} already exists.")
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
                has_internship = request.POST.get("has_internship") == 'true' if course_type == "M.Tech" else False
                
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
            messages.error(request, "User already exists.")
            return HttpResponseRedirect(reverse('add_student'))

        except Exception as e:
            logger.error(f"Error creating student: {e}")
            messages.error(request, "An error occurred while creating the student.")
            user.delete()
            return HttpResponseRedirect(reverse('add_student'))

        return HttpResponseRedirect(reverse('home'))

    else:
        new_student = MyUser.objects.exclude(student__isnull=False).exclude(faculty__isnull=False)
        return render(request, "Allocator/add_student.html", {
            "users": new_student
        })

@authorize_resource
def edit_student(request, id):
    student = get_object_or_404(Student, user_id=id)

    if request.method == "POST":
        student.user.first_name = request.POST.get("fname")
        student.user.last_name = request.POST.get("lname")
        student.user.email = request.POST.get("email")
        student.user.mobile_number = request.POST.get("mobile_number")
        student.has_backlog = request.POST.get("has_backlog") == "true"
        
        # Validate CGPA
        try:
            cgpa = float(request.POST.get("cgpa"))
            if cgpa < 0.0 or cgpa > 10.0:
                messages.error(request, "CGPA must be between 0.0 and 10.0.")
                return redirect("edit_student", id=id)
            student.cgpa = cgpa
        except ValueError:
            messages.error(request, "CGPA is not a valid number.")
            return redirect("edit_student", id=id)

        # Validate Academic Year
        academic_year = request.POST.get("academic_year")
        if not academic_year.isdigit() or len(academic_year) != 4:
            messages.error(request, "Academic year must be a 4-digit number.")
            return redirect("edit_student", id=id)
        student.academic_year = academic_year

        # Validate Branch
        branch = request.POST.get("branch")
        if branch not in ["AI", "IT"]:
            messages.error(request, "Branch must be either 'AI' or 'IT'.")
            return redirect("edit_student", id=id)
        student.branch = branch

        # Validate Mobile Number
        mobile_number = request.POST.get("mobile_number")
        if not re.fullmatch(r'^\d{10}$', mobile_number):
            messages.error(request, "Mobile number must be exactly 10 digits.")
            return redirect("edit_student", id=id)

        student.user.save()
        student.save()

        messages.success(request, "Student details updated successfully!")
        return redirect("all_student")

    return render(request, "Allocator/edit_student.html", {"student": student})

@authorize_resource
def delete_student(request, id):
    student = get_object_or_404(Student, user_id=id)

    if request.method == "POST":
        student.user.delete()  # Deleting user also deletes the associated Student record
        messages.success(request, "Student deleted successfully!")
        return redirect("all_student")

    return render(request, "Allocator/delete_student.html", {"student": student})

@authorize_resource
def all_student(request):
    students = Student.objects.all()
    return render(request, "Allocator/all_student.html", {"students": students})
