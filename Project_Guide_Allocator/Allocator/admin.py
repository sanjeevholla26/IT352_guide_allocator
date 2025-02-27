from django.contrib import admin
from .models import MyUser, Student, Faculty, AllocationEvent, ChoiceList, Clashes, Role, Permission
# Register your models here.
admin.site.register(MyUser)
admin.site.register(Student)
admin.site.register(Faculty)
admin.site.register(AllocationEvent)
admin.site.register(ChoiceList)
admin.site.register(Clashes)
admin.site.register(Role)
admin.site.register(Permission)

