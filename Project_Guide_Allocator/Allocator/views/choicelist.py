from django.http import HttpResponseRedirect
from django.contrib import messages
from django.shortcuts import render, redirect
from django.urls import reverse
from django.contrib.auth import logout
from ..decorators import authorize_resource
from ..models import AllocationEvent, Faculty, Student, ChoiceList, MyUser
from Project_Guide_Allocator.settings import SWIFT_OTP
from ..email_sender import send_mail_page
from .home import home
import logging
import random

logger = logging.getLogger('django')

def choice_locking_message(choice):
    recv_name = "User"
    if choice.student.user.first_name:
        recv_name = choice.student.user.first_name
    message = "Dear student,\n"
    preferences = ""
    for pref in choice.preference_list:
        get_u = MyUser.objects.get(id=pref["facultyID"])
        get_fac = Faculty.objects.get(user=get_u)
        preferences = preferences + f"{pref['choiceNo']} : {get_fac}\n"
    message = message + f"\nYou have successfully locked the below choices for the event {choice.event.event_name}:\n{preferences}\nWe wish you the best for your allocations."
    message = message + "\nThank you,\nBTech Major Project Allocation Team"
    return message

def generate_otp():
    if SWIFT_OTP:
        return 1
    return random.randint(100000, 999999)    

def send_to_otp(user):
    print(user.edu_email)
    user.otp = None
    user.save()
    user.otp = generate_otp()
    user.save()
    recv_name = "User"
    if user.first_name:
        recv_name = user.first_name
    if not SWIFT_OTP:
        send_mail_page(user.edu_email, 'Choice Locking OTP', f"Dear {recv_name},\nYour Choice Locking OTP(One Time Password) is {user.otp}. Kindly use this OTP to login.\nThank you.\nB.Tech Major Project Team.")

@authorize_resource
def choice_lock_otp(request, id):
    if request.user.is_authenticated:
        if request.method == "POST" :
            user = request.user
            choice = ChoiceList.objects.get(id=id)
            otp = request.POST["otp_entry"]
            if user and user.otp == otp:
                ChoiceList.objects.update_choice_list(choice_list=choice,is_locked=True)
                logger.info(f"User: {user.username} locked choices as {choice.preference_list}")
                # get_prev_choice.is_locked=True
                # get_prev_choice.save()
                send_mail_page(user.edu_email, "Choice Locking", choice_locking_message(choice))
                messages.error(request, "Your choices have been locked.")
                return HttpResponseRedirect(reverse('create_or_edit_choicelist', args=(choice.event.id,)))
            else :
                messages.error(request, f"Invalid OTP.")
                logout(request)
                return HttpResponseRedirect(reverse(home))
        else :
            return HttpResponseRedirect(reverse(home))
    else :
        return HttpResponseRedirect(reverse(home))
    
@authorize_resource
def create_or_edit_choicelist(request, id):
    e = AllocationEvent.objects.get(id=id)
    user_branch = request.user.student.branch
    user_batch = request.user.student.academic_year
    event_batch = e.eligible_batch
    user_course = request.user.student.course_type
    user_internship = request.user.student.has_internship
    project_type_check = True
    if e.project_type == 'B.Tech':
        project_type_check = user_course=="B.Tech"
    elif e.project_type == 'M.Tech Minor':
        project_type_check = (user_course=="M.Tech" and not user_internship)
    else:
        project_type_check = user_course=="M.Tech"
    if isinstance(event_batch, str) and event_batch.isdigit():
        event_batch=int(event_batch)
    if not user_branch == e.eligible_branch or not user_batch == event_batch or not project_type_check:
        return HttpResponseRedirect(reverse('home'))
    else:
        if request.method == "POST":
            action = request.POST.get('action')
            if action != 'lock':
                preference_list = []
                curr_student = Student.objects.get(user=request.user)
                for i in range(1, e.eligible_faculties.count() + 1):
                    faculty_id = request.POST.get(f'faculty_{i}')
                    if faculty_id:
                        preference_list.append({"choiceNo": i, "facultyID": faculty_id})
                try:
                    get_prev_choice = ChoiceList.objects.get(event=e, student=curr_student)
                    ChoiceList.objects.update_choice_list(choice_list=get_prev_choice,preference_list=preference_list)
                    logger.info(f"User: {curr_student.user.username} updated choices to {preference_list}")
                    # get_prev_choice.preference_list = preference_list
                    # get_prev_choice.save()
                except ChoiceList.DoesNotExist:
                    ChoiceList.objects.create_choice_list(event=e,student=request.user.student,preference_list=preference_list,cluster_number=1)
                    logger.info(f"User: {curr_student.user.username} created choices as {preference_list}")
                return HttpResponseRedirect(reverse('events'))
            else:
                curr_student = Student.objects.get(user=request.user)
                choice = ChoiceList.objects.get(event=e, student=curr_student)
                send_to_otp(request.user)
                messages.error(request, f"OTP has been mailed.")
                return render(request, "choice_lock_otp.html", {'id': choice.id})
        else:
            preference_range = range(1, e.eligible_faculties.count() + 1)
            curr_student = Student.objects.get(user=request.user)
            try:
                get_prev_choice = ChoiceList.objects.get(event=e, student=curr_student)
            except ChoiceList.DoesNotExist:
                get_prev_choice = None

            if get_prev_choice:
                locked = ChoiceList.objects.get(event=e, student=curr_student).is_locked
            else:
                locked = False
            preferences = {}
            if get_prev_choice:
                for pref in get_prev_choice.preference_list:
                    get_u = MyUser.objects.get(id=pref["facultyID"])
                    get_fac = Faculty.objects.get(user=get_u)
                    preferences[pref["choiceNo"]] = get_fac
            return render(request, "Allocator/event.html", {'event': e, 'preference_range': preference_range, 'filled_preference': preferences, 'filled_choice': get_prev_choice,'locked':locked})
