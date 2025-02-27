import functools
from django.shortcuts import HttpResponseRedirect
from django.urls import reverse
from django.contrib import messages
from .models import Role

def authorize_resource(func):
    @functools.wraps(func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, "You need to log in to access this page.")
            return HttpResponseRedirect(reverse("login"))
        # Capture the name of the action (function name)
        action_name = func.__name__

        # Capture the app name from the module
        module_name = func.__module__  # This returns the full module path (e.g., 'allocator.views')
        app_name = module_name.split('.')[0]  # Extract the app name by splitting the module path
        all_actions = Role.get_all_permissions(request.user)
        if not app_name in all_actions or not action_name in all_actions[app_name]:
            messages.error(request, "You do not have permission to access this page.")
            return HttpResponseRedirect(reverse("home"))
        # Call the original function
        return func(request, *args, **kwargs)

    return wrapper
