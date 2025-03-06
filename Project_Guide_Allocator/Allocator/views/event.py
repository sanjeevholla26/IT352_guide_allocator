from django.http import HttpResponseRedirect
from django.shortcuts import render, redirect
from django.urls import reverse
from ..decorators import authorize_resource
from ..models import AllocationEvent, Faculty,Student
from django.shortcuts import get_object_or_404
from django.contrib import messages
from django.utils import timezone
from datetime import datetime

import logging

logger = logging.getLogger('django')


@authorize_resource
def add_event(request):
    if request.method == "POST":
        user = request.user
        name = request.POST.get("name")
        start_datetime_str = request.POST.get("start_datetime")
        if start_datetime_str:
            naive_start_datetime = datetime.strptime(start_datetime_str, "%Y-%m-%dT%H:%M")  # Parse naive datetime
            start_datetime = timezone.make_aware(naive_start_datetime)
        end_datetime_str = request.POST.get("end_datetime")
        if end_datetime_str:
            naive_end_datetime = datetime.strptime(end_datetime_str, "%Y-%m-%dT%H:%M")  # Parse naive datetime
            end_datetime = timezone.make_aware(naive_end_datetime)
        batch = request.POST.get("batch")
        if batch and batch.isdigit():
            batch = int(batch)
        branch = request.POST.get("branch")
        project_type = request.POST.get("project_type")
        faculties = request.POST.getlist("faculties")
        AllocationEvent.objects.create_event(user=user, name=name, project_type=project_type, start_datetime=start_datetime, end_datetime=end_datetime, batch=batch, branch=branch, faculties=faculties)
        logger.info(f"User: Admin created event {name}")
        # new_event = AllocationEvent(
        #     owner=user,  # Set the owner to the current user
        #     event_name=name,
        #     start_datetime=start_datetime,
        #     end_datetime=end_datetime,
        #     eligible_batch=batch,
        #     eligible_branch=branch
        # )

        # new_event.save()  # Save the AllocationEvent instance first to get an ID

        # # Now add the selected faculties to the ManyToMany field
        # new_event.eligible_faculties.set(faculties)  # Set the ManyToMany relationship

        return HttpResponseRedirect(reverse('home'))  # Redirect after saving
    else:
        all_users = Faculty.objects.all()
        return render(request, "Allocator/add_event.html", {
            "faculties": all_users
        })

@authorize_resource
def edit_event(request, id):
    event = get_object_or_404(AllocationEvent, id=id)  # Get the event instance
    if request.method == 'POST':
        AllocationEvent.objects.update_event(event=event, name=request.POST.get('name'), project_type=request.POST.get('project_type'), start_datetime=request.POST.get('start_datetime'), end_datetime=request.POST.get('end_datetime'), batch=request.POST.get('batch'), branch=request.POST.get('branch'), faculties=request.POST.getlist('faculties'))
        logger.info(f"User: Admin updated event {request.POST.get('name')}")
        # Handle form submission
        # event.event_name = request.POST.get('name')
        # event.start_datetime = request.POST.get('start_datetime')
        # event.end_datetime = request.POST.get('end_datetime')
        # event.eligible_batch = request.POST.get('batch')
        # event.eligible_branch = request.POST.get('branch')
        # faculty_ids = request.POST.getlist('faculties')
        # event.eligible_faculties.set(faculty_ids)

        # event.save()
        return redirect('home')  # Redirect to a success page or home
    else:
        # For GET request, render the form with existing values
        faculties = Faculty.objects.all()  
        return render(request, 'Allocator/edit_event.html', {
            'event': event,
            'faculties': faculties
        })


@authorize_resource
def all_events(request): # needs changes
    if request.method == "GET":
        # active_events = AllocationEvent.active_events()
        active_events = AllocationEvent.objects.all()
        user_branch = request.user.student.branch
        user_batch = request.user.student.academic_year
        user_backlog=request.user.student.has_backlog
        student=request.user.student
        if user_backlog is False:
            eligible_events = active_events.filter(eligible_batch=user_batch, eligible_branch=user_branch)
            if student.course_type == 'B.Tech':
                eligible_events = active_events.filter(project_type="B.Tech")
            elif not student.has_internship:
                eligible_events = [event for event in active_events if event.project_type in {"M.Tech Major", "M.Tech Minor"}]
            else:
                eligible_events = active_events.filter(project_type="M.Tech Major")

            return render(request, "Allocator/all_events.html", {
                "events" : eligible_events
            })
        else:
            eligible_events=active_events.filter(for_backlog=True)
            res=[]
            for event in eligible_events:
                if event.eligible_students.filter(pk=student.pk).exists():  # Check if student is in eligible_students
                    res.append(event)

            return render(request, "Allocator/all_events.html", {
                "events" : res
            })
    else:
        return HttpResponseRedirect(reverse('home'))


@authorize_resource
def admin_all_events(request):
    if request.method == "GET":
        all_events = AllocationEvent.objects.all()
        now = timezone.now()  # Get the current time
        # Create a list of booleans where True means the event is active (before end_datetime)
        for event in all_events:
            event.is_active = event.end_datetime >= now
        return render(request, "Allocator/admin_all_events.html", {
            "events" : all_events,
        })
    else:
        return HttpResponseRedirect(reverse('home'))

@authorize_resource
def eligible_events(request):
    if request.method == "GET":
        fac = Faculty.objects.get(user=request.user)
        get_eligible_events = fac.eligible_faculty_events.all()

        return render(request, "Allocator/eligible_events.html", {
            "eligible_events": get_eligible_events
        })
    else:
        messages.error(request, "Invalid request method")
        return HttpResponseRedirect(reverse('home'))

@authorize_resource
def event_results(request, id):
    if request.method == "GET":
        event = AllocationEvent.objects.get(id=id)
        get_fac = Faculty.objects.get(user=request.user)
        allocated_choices = get_fac.allocated_choices.filter(event=event)

        return render(request, "Allocator/event_result.html", {
            "allocated_choices": allocated_choices
        })
    else:
        messages.error(request, "Invalid request method")
        return HttpResponseRedirect(reverse('home'))

def add_backlog(request,id):
    if request.method=="GET":
        event = get_object_or_404(AllocationEvent, id=id)
        students=Student.objects.all()
        if event.project_type == "B.Tech":
            students = students.filter(course_type="B.Tech")
        elif event.project_type == "M.Tech Minor":
            students = students.filter(course_type="M.Tech", has_internship=False)
        else:
            students = students.filter(course_type="M.Tech")
        backlog_students = students.filter(has_backlog=True)
        existing_backlogs = event.eligible_students.all()
        return render(request,"add_backlog.html",{
            "id":id,
            "students":backlog_students,
            "existing_backlogs":existing_backlogs
        })
    else:
        event = get_object_or_404(AllocationEvent, id=id)  # Get the event instance
        students = request.POST.getlist("students")
        # event.start_datetime = request.POST.get('start_datetime')
        # event.end_datetime = request.POST.get('end_datetime')
        event.for_backlog=True
        event.eligible_students.set(students)
        event.save()
        return redirect('home')  # Redirect to a success page or home