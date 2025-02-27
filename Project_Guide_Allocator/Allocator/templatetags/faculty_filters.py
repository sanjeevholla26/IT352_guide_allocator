from django import template
from Allocator.models import Faculty

register = template.Library()

@register.filter
def get_faculty_abbreviation(faculty_id):
    try:
        faculty = Faculty.objects.get(user__id=faculty_id)
        return faculty.abbreviation
    except Faculty.DoesNotExist:
        return ''  # Return empty string if faculty does not exist