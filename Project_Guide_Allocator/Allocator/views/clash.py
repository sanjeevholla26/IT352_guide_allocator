from django.http import HttpResponseRedirect
from django.shortcuts import render, redirect
from django.urls import reverse
from ..decorators import authorize_resource
from ..models import ChoiceList, Clashes, Faculty, MyUser, Student
from ..allocation_function import allocate
from django.contrib import messages
from datetime import timedelta
from django.utils.timezone import now
from django.contrib.auth.decorators import login_required

import logging

logger = logging.getLogger('django')

CLASH_TIMEOUT = timedelta(days=3)


@authorize_resource
def show_all_clashes(request):
    if request.method == "GET":
        get_fac = Faculty.objects.get(user=request.user)
        all_clashes = Clashes.objects.filter(faculty=get_fac, selected_student=None, is_processed=False)

        return render(request, "Allocator/all_clashes.html", {
            "clashes": all_clashes
        })

    else:
        return HttpResponseRedirect(reverse('home'))

@login_required
@authorize_resource
def resolve_clash(request, id):
    clash = Clashes.objects.get(id=id)
    students = clash.list_of_students.all()

    if(clash.faculty.user!=request.user):
        messages.error(request, "You cannot access this page.")
        return HttpResponseRedirect(reverse(show_all_clashes))

    preferences = []

    for s in students:
        chList = ChoiceList.objects.get(event=clash.event, student=s).printChoiceList()
        preferences.append([s.user.username, s.cgpa, chList])

    if request.method == "GET":
        return render(request, "Allocator/clash.html", {
            "clash": clash,
            "preferenceList": preferences
        })
    else:
        get_user_id = request.POST.get("student_id")
        user = MyUser.objects.get(id=get_user_id)
        selected_student = Student.objects.get(user=user)

        Clashes.objects.update_clash(clash=clash,selected_student = selected_student)
        logger.info(f"User: {clash.faculty.user.username} resolved clash in event {clash.event.event_name} in cluster {clash.cluster_id} to {selected_student.user.username} among {clash.list_of_students}")
        # clash.selected_student = selected_student
        # clash.save()
        allocate(clash.event.id)
        return HttpResponseRedirect(reverse(show_all_clashes))

@authorize_resource
def admin_show_clash(request):
    if request.method == "GET":
         # Assuming CLASH_TIMEOUT is a timedelta object
        timeout_limit = now() - CLASH_TIMEOUT

        # Filter clashes that are unprocessed and created more than CLASH_TIMEOUT ago
        all_clashes = Clashes.objects.filter(selected_student=None, is_processed=False, created_datetime__lte=timeout_limit)

        return render(request, "Allocator/admin_show_clash.html", {
            "clashes": all_clashes
        })

    else:
        return HttpResponseRedirect(reverse('home'))

@authorize_resource
def admin_resolve_clash(request, id):
    clash = Clashes.objects.get(id=id)
    students = clash.list_of_students.all()

    selected_student = students.order_by('-cgpa').first()

    Clashes.objects.update_clash(clash=clash,selected_student = selected_student)
    logger.info(f"User: Admin resolved clash in event {clash.event.event_name} in cluster {clash.cluster_id} to {selected_student.user.username} among {clash.list_of_students}")
    # clash.selected_student = selected_student
    # clash.save()
    allocate(clash.event.id)
    return HttpResponseRedirect(reverse(admin_show_clash))
