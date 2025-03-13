from django.http import HttpResponseRedirect
from django.shortcuts import render, redirect
from django.urls import reverse
from ..models import Student,Faculty
from ..email_sender import send_mail_page
from .authorization import generate_otp, password_creation
from django.contrib.auth.hashers import check_password, make_password
from django.contrib import messages
from Project_Guide_Allocator.settings import SWIFT_OTP

def home(request) :
    if not request.user.is_authenticated :
        return HttpResponseRedirect(reverse("login"))
    else :
        student = Student.objects.filter(user__id=request.user.id)
        if student:
            student = student.first()
        faculty = Faculty.objects.filter(user__id=request.user.id)
        if faculty:
            faculty = faculty.first()
        return render(request, "Allocator/home.html", {"student":student, "faculty":faculty})

def change_password(request):
    if not request.user.is_authenticated :
        return HttpResponseRedirect(reverse("login"))
    if request.method == "POST":
        current_password = request.POST.get("current_password")
        if not check_password(current_password, request.user.password):
            messages.error(request, "Current password is incorrect.")
            return redirect(home)
        if not request.POST.get("otp") == request.user.otp:
            messages.error(request, "OTP is wrong.")
            return redirect(home)
        return render(request, "Allocator/login_create_password.html", {
            "edu_email": request.user.edu_email,
            "change_password": True
        })
    else:
        user = request.user
        user.otp = generate_otp()
        user.save()
        recv_name = "User"
        if user.first_name:
            recv_name = user.first_name
        if not SWIFT_OTP:
            send_mail_page(user.edu_email, 'Password Change OTP', f"Dear {recv_name},\nYour OTP(One Time Password) for password change is {user.otp}. Kindly use this OTP to login.\nThank you.\nProject Guide Allocator Team.")
        return render(request, "Allocator/home_change_password.html")

def update_password(request):
    if not request.user.is_authenticated :
        return HttpResponseRedirect(reverse("login"))
    if request.method == "POST":
        return password_creation(request)
    else:
        return HttpResponseRedirect(reverse("home"))
