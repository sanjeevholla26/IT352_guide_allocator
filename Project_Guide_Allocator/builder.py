import os
import django

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Project_Guide_Allocator.settings')  # Ensure this is correct
django.setup()

admin_perms = "login,home,register,add_student,add_event,edit_event,add_faculty,admin_all_events,create_cluster,run_allocation,reset_allocation,admin_show_clash,admin_resolve_clash,add_permissions,generate_student_pdf,generate_faculty_pdf,generate_admin_pdf,event_results,logout_view,edit_faculty,delete_faculty,all_faculty,all_student,edit_student,delete_student"
student_perms = "all_events,event,create_or_edit_choicelist,choice_lock_otp,logout_view"
faculty_perms = "show_all_clashes,resolve_clash,eligible_events,logout_view,event_results"

app_name = 'Allocator'

# Import your models
from Allocator.models import Role, Permission

# Add data to the database
def add_data():
    # Create 'admin' role and permissions
    admin = Role(role_name="admin")
    admin.save()

    admin_perm = Permission(actions=admin_perms, app_name=app_name)
    admin_perm.save()
    admin_perm.role.set([admin])  # Wrap in list to avoid issues

    # Create 'student' role and permissions
    student = Role(role_name="student")
    student.save()

    student_perm = Permission(actions=student_perms, app_name=app_name)
    student_perm.save()
    student_perm.role.set([student])

    # Create 'faculty' role and permissions
    faculty = Role(role_name="faculty")
    faculty.save()

    faculty_perm = Permission(actions=faculty_perms, app_name=app_name)
    faculty_perm.save()
    faculty_perm.role.set([faculty])

if __name__ == "__main__":
    add_data()
    print("Data added successfully.")
