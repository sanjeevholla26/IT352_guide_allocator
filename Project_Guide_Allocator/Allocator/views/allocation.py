from django.http import HttpResponseRedirect
from django.utils import timezone
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from ..decorators import authorize_resource
from ..models import AllocationEvent, ChoiceList, Clashes,Faculty
from ..allocation_function import allocate

import logging

logger = logging.getLogger('django')

@authorize_resource
def create_cluster(request, id):
    get_event = AllocationEvent.objects.get(id=id)
    if get_event.status == 'open' and timezone.now() > get_event.end_datetime:
        get_event.status = 'locked'
        get_event.save()
    if request.method == "POST":
        # Use .count() to get the number of eligible faculties (many-to-many field)
        total_profs = get_event.eligible_faculties.count()

        # Get the list of ChoiceList objects sorted by student CGPA in descending order
        students_choice_list = ChoiceList.objects.filter(event=get_event).order_by('-student__cgpa', 'student__user__username')

        max_cluster_num = 0

        for i, choice in enumerate(students_choice_list):
            # Calculate the cluster number (integer division)
            cluster_no = (i // total_profs) + 1
            max_cluster_num = max(max_cluster_num, cluster_no)
            ChoiceList.objects.update_choice_list(choice_list=choice,cluster_number=cluster_no)
            # choice.cluster_number = cluster_no
            # choice.save()

        AllocationEvent.objects.update_event(get_event,cluster_count=max_cluster_num)
        logger.info(f"Admin created cluster for event : {get_event.event_name}")
        # get_event.cluster_count = max_cluster_num
        # get_event.save()

        # return HttpResponseRedirect(reverse(admin_all_events))
        return HttpResponseRedirect(reverse(create_cluster, args=(id, )))
    else:
        clusters = {}
        if get_event.for_backlog is False:
            students_choice_list = ChoiceList.objects.filter(event=get_event).order_by('-student__cgpa', 'student__user__username')
            allotment_complete = True
            if get_event.cluster_count != 0:
                for choice in students_choice_list:
                    cluster_no = choice.cluster_number
                    if cluster_no not in clusters:
                        clusters[cluster_no] = []
                    clusters[cluster_no].append(choice)
                    if not choice.current_allocation:
                        allotment_complete = False
            else:
                allotment_complete = False
            return render(request, "Allocator/create_cluster.html", {
                "event" : get_event,
                "clusters": clusters,
                "allotment_complete": allotment_complete,
            })
        else:
            students_choice_list = ChoiceList.objects.filter(event=get_event)
            backlog_choices = students_choice_list.filter(student__has_backlog=True).order_by('-student__cgpa', 'student__user__username')
            student_choices = students_choice_list.filter(student__has_backlog=False).order_by('-student__cgpa', 'student__user__username')
            allotment_complete = True
            if get_event.cluster_count != 0:
                for choice in student_choices:
                    cluster_no = choice.cluster_number
                    if cluster_no not in clusters:
                        clusters[cluster_no] = []
                    clusters[cluster_no].append(choice)
                    if not choice.current_allocation:
                        allotment_complete = False
            else:
                allotment_complete = False
            backlog_allocated = backlog_choices.filter(current_allocation__isnull=False)
            backlog_not_allocated = backlog_choices.filter(current_allocation__isnull=True)

            return render(request, "Allocator/create_cluster.html", {
                "event" : get_event,
                "clusters": clusters,
                "backlog":backlog_not_allocated,
                "backlog_alloted":backlog_allocated,
                "id":id,
                "allotment_complete": allotment_complete,
            })

@authorize_resource
def run_allocation(request, id):
    if request.method == "POST":
        allocate(id)
        get_event = AllocationEvent.objects.get(id=id)
        logger.info(f"Admin started allocation for event : {get_event.event_name}")
        return HttpResponseRedirect(reverse(create_cluster, args=(id, )))
    else:
        return HttpResponseRedirect(reverse('home'))

@authorize_resource
def reset_allocation(request, id):
    if request.method == "POST":
        get_event = AllocationEvent.objects.get(id=id)
        students_choice_list = ChoiceList.objects.filter(event=get_event)
        for s in students_choice_list:
            check_backlog=s.student.has_backlog
            if check_backlog is False:
                s.current_allocation = None
                s.current_index = 1
                s.save()

        clashes = Clashes.objects.filter(event=get_event)
        for c in clashes:
            c.is_processed = True
            c.save()
        logger.info(f"Admin reset allocation for event : {get_event.event_name}")
        return HttpResponseRedirect(reverse(create_cluster, args=(id, )))
    else:
        return HttpResponseRedirect(reverse('home'))
    

def allot_backlog(request, id):
    event = get_object_or_404(AllocationEvent, id=id)
    last_cluster=event.cluster_count

    if request.method == "POST":
        students = []
        faculties = []
        
        # Iterate through the POST data to extract the student-faculty pairs
        for key, value in request.POST.items():
            if key.startswith('student_'):
                choice_id = key.split('_')[1]
                student_id = value
                faculty_key = f'faculty_{choice_id}'
                
                # Get the corresponding faculty selection
                if faculty_key in request.POST:
                    faculty_id = request.POST[faculty_key]
                    students.append(int(student_id))
                    faculties.append(int(faculty_id))
        
        # Process the collected student and faculty data
        for student_id, faculty_id in zip(students, faculties):
            choice = ChoiceList.objects.get(student_id=student_id, event=event)
            
            # Find the corresponding faculty
            try:
                faculty = Faculty.objects.get(user__id=faculty_id)
                choice.current_allocation = faculty
                choice.cluster_number=last_cluster
                choice.save()
            except Faculty.DoesNotExist:
                print(f"Faculty with user ID {faculty_id} not found")

        # After saving the data, redirect to a success page or home
        return redirect('home')  # Redirect to the appropriate view after processing

    else:
        event = AllocationEvent.objects.get(id=id)
        backlog_alloted = ChoiceList.objects.filter(event=event)

        # Prepare the faculty abbreviations for the template
        faculty_abbreviations = [faculty.abbreviation for faculty in Faculty.objects.all()]

        return render(request, 'create_cluster.html', {
            'backlog_alloted': backlog_alloted,
            'faculty_abbreviations': faculty_abbreviations,  # Include all faculty abbreviations
        })
