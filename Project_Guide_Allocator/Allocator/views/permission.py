from django.http import HttpResponseRedirect
from django.shortcuts import render, redirect
from django.urls import reverse
from ..decorators import authorize_resource
from ..models import Permission, Role

@authorize_resource
def add_permissions(request):
    if request.method == "POST":
        new_permissions = request.POST["permissions"]
        app_name = request.POST["app_name"]
        roles_list = request.POST.getlist("roles_list")


        new_perms = Permission(actions=new_permissions, app_name=app_name)
        new_perms.save()

        new_perms.role.set(roles_list)

        return HttpResponseRedirect(reverse('home'))

    else:
        all_roles = Role.objects.all()
        return render(request, "Allocator/add_permissions.html", {
            "roles": all_roles
        })
