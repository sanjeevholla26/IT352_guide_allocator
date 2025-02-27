import re
import csv
import io
from django.db import IntegrityError
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.shortcuts import render, redirect
from django.urls import reverse
from ..decorators import authorize_resource
from ..models import MyUser, Role, Faculty

import logging

logger = logging.getLogger('django')

@authorize_resource
def add_faculty(request):
    if request.method == "POST":
        if 'csv_file' in request.FILES:
            csv_file = request.FILES['csv_file']
            if not csv_file.name.endswith('.csv'):
                messages.error(request, "Invalid file format. Please upload a CSV file.")
                return redirect('add_faculty')
            
            data_set = csv_file.read().decode('UTF-8')
            io_string = io.StringIO(data_set)
            next(io_string)  # Skip header row if present

            added_faculties = 0
            for row in csv.reader(io_string, delimiter=',', quotechar='"'):
                try:
                    edu_email, email, username, fname, lname, mobile_number, abbreviation = row
                    if not edu_email.endswith("@nitk.edu.in"):
                        messages.error(request, f"Invalid NITK email for {username}.")
                        continue
                    if not re.fullmatch(r'^\d{10}$', mobile_number):
                        messages.error(request, f"Invalid mobile number for {username}.")
                        continue
                    user = MyUser.objects.create_user(
                        edu_email=edu_email, email=email, username=username,
                        first_name=fname, last_name=lname, mobile_number=mobile_number
                    )
                    Faculty.objects.create_faculty(user=user, abbreviation=abbreviation)
                    faculty_role, _ = Role.objects.get_or_create(role_name="faculty")
                    faculty_role.users.add(user)
                    logger.info(f"User: {username} added as Faculty via CSV upload")
                    added_faculties += 1
                except IntegrityError:
                    messages.error(request, f"Employee ID {username} already exists.")
                except Exception as e:
                    messages.error(request, f"Error processing row: {row}, {str(e)}")
            messages.success(request, f"{added_faculties} faculties added successfully!")
            return redirect('add_faculty')
        
        edu_email = request.POST.get("edu_mail")
        if not edu_email.endswith("@nitk.edu.in"):
            messages.error(request, "The Email ID must be an NITK edu mail ID.")
            return redirect('add_faculty')
        
        email = request.POST.get("email")
        username = request.POST.get("username")
        mobile_number = request.POST.get("mobile_number")
        fname = request.POST.get("fname")
        lname = request.POST.get("lname")
        
        if not re.fullmatch(r'^\d{10}$', mobile_number):
            messages.error(request, "Mobile number must be exactly 10 digits.")
            return redirect('add_faculty')
        
        try:
            user = MyUser.objects.create_user(
                edu_email=edu_email, email=email, username=username,
                first_name=fname, last_name=lname, mobile_number=mobile_number
            )
        except IntegrityError:
            messages.error(request, "Employee ID already exists.")
            return redirect('add_faculty')
        
        abbreviation = request.POST.get("abbreviation")
        Faculty.objects.create_faculty(user=user, abbreviation=abbreviation)
        
        faculty_role, _ = Role.objects.get_or_create(role_name="faculty")
        faculty_role.users.add(user)
        logger.info(f"User: {user.username} added as Faculty")
        
        return redirect('home')
    
    new_faculty = MyUser.objects.exclude(faculty__isnull=False).exclude(student__isnull=False)
    return render(request, "Allocator/add_faculty.html", {"users": new_faculty})
