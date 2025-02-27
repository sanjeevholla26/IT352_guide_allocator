from django.http import HttpResponseRedirect
from django.shortcuts import render, redirect
from django.urls import reverse


def home(request) :
    if not request.user.is_authenticated :
        return HttpResponseRedirect(reverse("login"))
    else :
        return render(request, "Allocator/home.html")

