from django.http import HttpResponseRedirect
from django.shortcuts import render, redirect
from django.urls import reverse
from ..decorators import authorize_resource
from ..models import MyUser, Role
from django.contrib import messages
from ..email_sender import send_mail_page
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.hashers import check_password
from django.urls import reverse
from django.urls import reverse
from captcha.models import CaptchaStore
from Project_Guide_Allocator.settings import ADMIN_BYPASS, QUICK_LOGIN, SWIFT_OTP, FAILS_COUNT, FAILS_DELAY, RESET_DELAY, CAPTCHA_SECRET_KEY
from django.utils import timezone
from datetime import timedelta
import requests
import random
import logging
from twilio.rest import Client
from django.conf import settings
import pytz

logger = logging.getLogger('django')

def blocked_time(user):
    ist = pytz.timezone('Asia/Kolkata')
    blocked_time_ist = user.pswd_blocked.astimezone(ist)
    return blocked_time_ist.strftime('%d %B %Y, %I:%M %p')

def generate_otp():
    if SWIFT_OTP:
        return 1
    return random.randint(100000, 999999)

# def generate_captcha():
#     captcha_key = CaptchaStore.generate_key()
#     captcha_image = captcha_image_url(captcha_key)
#     result = ""
#     if QUICK_LOGIN:
#         result = CaptchaStore.objects.get(hashkey=captcha_key).response
#     return [captcha_key, captcha_image, result]

def send_sms(mobile_number, otp, recv_name):
    account_sid = settings.TWILIO_ACCOUNT_SID
    auth_token = settings.TWILIO_AUTH_TOKEN
    twilio_phone_number = settings.TWILIO_PHONE_NUMBER

    client = Client(account_sid, auth_token)

    message = client.messages.create(
        body=f"Dear {recv_name},\nYour Login OTP (One Time Password) is {otp}. Kindly use this OTP to login.\nThank you.\nB.Tech Major Project Team.",
        from_=twilio_phone_number,
        to=f'+91{mobile_number}'
    )
    return message.sid

def send_to_otp(request, user, next_url):
    user.otp = None
    user.save()
    user.otp = generate_otp()
    user.save()
    recv_name = "User"
    if user.first_name:
        recv_name = user.first_name
    if not SWIFT_OTP:
        send_mail_page(user.edu_email, 'Login OTP', f"Dear {recv_name},\nYour Login OTP(One Time Password) is {user.otp}. Kindly use this OTP to login.\nThank you.\nB.Tech Major Project Team.")
        # if user.mobile_number:
        #     send_sms(user.mobile_number, user.otp, recv_name)
    return render(request, "Allocator/login_otp.html", {
            "message": "OTP has been sent to your email. Please enter it below.",
            "next": next_url,
            "edu_email": user.edu_email
        })

def is_user_blocked(user):
    if user.failed_blocked and user.failed_blocked > timezone.now():
        return True
    return False

def failed_attempt(edu_email):
    try:
        user = MyUser.objects.get(edu_email=edu_email)
        user.failed_attempts = user.failed_attempts + 1
        user.save()
        if user.failed_attempts >= FAILS_COUNT:
            user.failed_blocked = timezone.now() + timedelta(minutes=FAILS_DELAY)
            user.failed_attempts = 0
            user.save()
            return f"User has been blocked till {user.failed_blocked}."
        else:
            return f"User has {FAILS_COUNT-user.failed_attempts} login attempts left."
    except MyUser.DoesNotExist:
        return ""

def logged_in(user):
    user.failed_attempts = 0
    user.save()

def verify_recaptcha(response):
    secret_key = CAPTCHA_SECRET_KEY  # Store your secret key in settings
    data = {
        'secret': secret_key,
        'response': response
    }
    r = requests.post('https://www.google.com/recaptcha/api/siteverify', data=data)
    result = r.json()
    return result.get('success', False)

def login_view(request):
    if not request.user.is_authenticated:
        if request.method == "POST":
            edu_email = request.POST["edu_email"]
            next_url = request.POST.get("next", "")
            try:
                user = MyUser.objects.get(edu_email=edu_email)
            except MyUser.DoesNotExist:
                messages.error(request, "User does not exist.")
                return HttpResponseRedirect(reverse(login_view))
            if not user:
                messages.error(request, "Invalid username.")
                return HttpResponseRedirect(reverse(login_view))
            if is_user_blocked(user):
                messages.error(request, f"User is blocked. Wait till {user.failed_blocked} to login.")
                return HttpResponseRedirect(reverse(login_view))
            recaptcha_response = request.POST.get('g-recaptcha-response')  # Get reCAPTCHA response
            if ADMIN_BYPASS:
                admin_role = Role.objects.get(role_name='admin')
                if admin_role in user.roles.all():
                    return render(request, "Allocator/login_password.html", {
                    "next": next_url,
                    "edu_email": edu_email
                    })
            try:
                if not verify_recaptcha(recaptcha_response) and not QUICK_LOGIN:  # Verify reCAPTCHA
                    messages.error(request, "Invalid reCAPTCHA. Please try again.")
                    return HttpResponseRedirect(reverse(login_view))
                else:
                    if user.is_registered:
                        return render(request, "Allocator/login_password.html", {
                            "next": next_url,
                            "edu_email": edu_email
                        })
                    else:
                        if QUICK_LOGIN:
                            return render(request, "Allocator/login_create_password.html", {
                                "next": next_url,
                                "edu_email": edu_email
                            })
                        else:
                            return send_to_otp(request, user, next_url)
            except CaptchaStore.DoesNotExist:
                messages.error(request, "Captcha validation error. Please try again.")
                return HttpResponseRedirect(reverse(login_view))
        else:
            return render(request, "Allocator/login.html")
    else:
        return HttpResponseRedirect(reverse('home'))


def otp(request) :
    if not request.user.is_authenticated:
        if request.method == "POST" :
            edu_email = request.POST["edu_email"]
            otp = request.POST["otp_entry"]
            next_url = request.POST["next"]
            user = MyUser.objects.get(edu_email=edu_email)

            if user and user.otp == otp:
                if is_user_blocked(user):
                    messages.error(request, f"User is blocked. Wait till {user.failed_blocked} to login.")
                    return HttpResponseRedirect(reverse(login_view))
                if user.is_registered:
                    login(request, user)
                    logged_in(user)
                    return HttpResponseRedirect(next_url if next_url else reverse('home'))
                else:
                    return render(request, "Allocator/login_create_password.html", {
                        "next": next_url,
                        "edu_email": edu_email
                    })
            else :
                messages.error(request, f"Invalid OTP. Kindly restart the login. {failed_attempt(edu_email)}")
                return HttpResponseRedirect(reverse(login_view))
        else :
            return HttpResponseRedirect(reverse(login_view))
    else :
        return HttpResponseRedirect(reverse('home'))

def validatePassword(password):
    # return True
    length = len(password)
    digits = sum(map(str.isdigit, password))
    alphas = sum(map(str.isalpha, password))
    others = length - digits - alphas
    upper = sum(map(str.isupper, password))
    result = length>=6 and digits>=1 and alphas>=1 and others>=1 and upper>=1 and upper!=alphas
    return result

def password_creation(request):
    edu_email = request.POST["edu_email"]
    password = request.POST["password"]
    repassword = request.POST["repassword"]
    next_url = request.POST["next"]
    user = MyUser.objects.get(edu_email=edu_email)
    if not user:
        messages.error(request, "Invalid user.")
        return HttpResponseRedirect(reverse(login_view))
    if is_user_blocked(user):
        messages.error(request, f"User is blocked. Wait till {user.failed_blocked} to login.")
        return HttpResponseRedirect(reverse(login_view))
    if password != repassword:
        return render(request, "Allocator/login_create_password.html", {
            "message" : "Passwords don't match.",
            "next": next_url,
            "edu_email": edu_email
        })
    if validatePassword(password):
        # print(user.password)
        # print(password)
        # print(check_password(password, user.password))
        if user.is_registered and check_password(password, user.password):
            messages.error(request, "New password is the same as Old password.")
            return HttpResponseRedirect(reverse("home"))
        user.otp=None
        user.set_password(password)
        user.is_registered = True
        user.pswd_blocked = timezone.now() + timedelta(hours=RESET_DELAY)
        user.save()
        authenticate(request, edu_email=edu_email, password=password)
        login(request, user)
        logged_in(user)
        messages.success(request, "New Password created successfully.")
        return HttpResponseRedirect(next_url if next_url else reverse('home'))
    else:
        return render(request, "Allocator/login_create_password.html", {
            "message" : "Invalid password format. Kindly read the rules and try again.",
            "next": next_url,
            "edu_email": edu_email
        })

def create_password(request) :
    if not request.user.is_authenticated:
        if request.method == "POST" :
            return password_creation(request)
        else :
            return HttpResponseRedirect(reverse(login_view))
    else :
        return HttpResponseRedirect(reverse('home'))

def complete_login(request) :
    if not request.user.is_authenticated:
        if request.method == "POST" :
            edu_email = request.POST["edu_email"]
            password = request.POST["password"]
            next_url = request.POST["next"]
            user = authenticate(request, edu_email=edu_email, password=password)
            # logger.info(f"User: {user.username} logged in")
            if user is not None :
                if is_user_blocked(user):
                    messages.error(request, f"User is blocked. Wait till {user.failed_blocked} to login.")
                    return HttpResponseRedirect(reverse(login_view))
                admin_role = Role.objects.get(role_name='admin')
                if (ADMIN_BYPASS and admin_role in user.roles.all()) or QUICK_LOGIN:
                    login(request, user)
                    logged_in(user)
                    return HttpResponseRedirect(next_url if next_url else reverse('home'))
                else:
                    return send_to_otp(request, user, next_url)
            else:
                logger.exception(f"IP: {request.META.get('REMOTE_ADDR')} failed to login")
                messages.error(request, f"Wrong Password. Kindly try again. {failed_attempt(edu_email)}")
                return HttpResponseRedirect(reverse(login_view))
        else :
            return HttpResponseRedirect(reverse(login_view))
    else :
        return HttpResponseRedirect(reverse('home'))

def forgot_password(request) :
    if not request.user.is_authenticated:
        if request.method == "POST" :
            edu_email = request.POST["edu_email"]
            user =  MyUser.objects.get(edu_email=edu_email)
            # logger.info(f"User: {user.username} logged in")
            if user is not None :
                if is_user_blocked(user):
                    messages.error(request, f"User is blocked. Wait till {user.failed_blocked} to login.")
                    return HttpResponseRedirect(reverse(login_view))
                if user.pswd_blocked and user.pswd_blocked > timezone.now():
                    messages.error(request, f"User is blocked. Wait till {blocked_time(user)} to reset password.")
                    return HttpResponseRedirect(reverse(login_view))
                user.otp = None
                user.save()
                user.otp = generate_otp()
                user.save()
                recv_name = "User"
                if user.first_name:
                    recv_name = user.first_name
                if not SWIFT_OTP:
                    send_mail_page(user.edu_email, 'Password reset OTP', f"Dear {recv_name},\nYour password reset OTP(One Time Password) is {user.otp}. Kindly use this OTP to reset your password.\nThank you.\nProject Guide Allocator Team.")
                return render(request, "Allocator/login_otp.html", {"message": "OTP has been sent to your email. Please enter it below.","edu_email": user.edu_email, "reset_pswd": True, "next_url": None})
            else:
                logger.exception(f"IP: {request.META.get('REMOTE_ADDR')} failed to login")
                messages.error(request, f"Wrong Password. Kindly try again. {failed_attempt(edu_email)}")
                return HttpResponseRedirect(reverse(login_view))
        else :
            return HttpResponseRedirect(reverse(login_view))
    else :
        return HttpResponseRedirect(reverse('home'))

def forgot_password_otp(request) :
    if not request.user.is_authenticated:
        if request.method == "POST" :
            edu_email = request.POST["edu_email"]
            user =  MyUser.objects.get(edu_email=edu_email)
            # logger.info(f"User: {user.username} logged in")
            if user is not None :
                if is_user_blocked(user):
                    messages.error(request, f"User is blocked. Wait till {user.failed_blocked} to login.")
                    return HttpResponseRedirect(reverse(login_view))
                if user.pswd_blocked and user.pswd_blocked > timezone.now():
                    messages.error(request, f"User is blocked. Wait till {blocked_time(user)} to reset password.")
                    return HttpResponseRedirect(reverse(login_view))
                user.otp = None
                user.is_registered=False
                user.pswd_blocked = timezone.now() + timedelta(hours=RESET_DELAY)
                user.save()
                recv_name = "User"
                if user.first_name:
                    recv_name = user.first_name
                send_mail_page(user.edu_email, 'Password Reset Confirmed', f"Dear {recv_name},\nYour password has been reset. Kindly login again to set a new password.\nThank you.\nProject Guide Allocator Team.")
                messages.success(request, f"Your password has been reset, kindly relogin to create a new passwod.")
                return HttpResponseRedirect(reverse('home'))
            else:
                logger.exception(f"IP: {request.META.get('REMOTE_ADDR')} failed to login")
                messages.error(request, f"Wrong Password. Kindly try again. {failed_attempt(edu_email)}")
                return HttpResponseRedirect(reverse(login_view))
        else :
            return HttpResponseRedirect(reverse(login_view))
    else :
        return HttpResponseRedirect(reverse('home'))

def logout_view(request) :
    if request.user.is_authenticated:
        logger.info(f"User: {request.user.username} logged out")
        logout(request)
        return HttpResponseRedirect(reverse('login'))
