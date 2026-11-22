from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from .forms import StaffCreateForm, StaffEditForm
from .models import StaffProfile
from .permissions import admin_required, manager_required


def login_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard:home")
    if request.method == "POST":
        username = request.POST.get("username", "")
        password = request.POST.get("password", "")
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect("dashboard:home")
        messages.error(request, "Invalid username or password.")
    return render(request, "accounts/login.html")


@login_required
def logout_view(request):
    logout(request)
    return redirect("accounts:login")


@manager_required
def staff_list(request):
    staff = StaffProfile.objects.select_related("user").all()
    return render(request, "accounts/staff_list.html", {"staff": staff})


@admin_required
def staff_create(request):
    if request.method == "POST":
        form = StaffCreateForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Staff member added.")
            return redirect("accounts:staff_list")
    else:
        form = StaffCreateForm()
    return render(request, "accounts/staff_form.html", {"form": form, "title": "Add Staff Member"})


@admin_required
def staff_edit(request, pk):
    profile = get_object_or_404(StaffProfile, pk=pk)
    if request.method == "POST":
        form = StaffEditForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, "Staff record updated.")
            return redirect("accounts:staff_list")
    else:
        form = StaffEditForm(instance=profile)
    return render(request, "accounts/staff_form.html", {"form": form, "title": f"Edit {profile.user.username}"})


@admin_required
def staff_delete(request, pk):
    profile = get_object_or_404(StaffProfile, pk=pk)
    if request.method == "POST":
        user = profile.user
        user.delete()
        messages.success(request, "Staff member removed.")
        return redirect("accounts:staff_list")
    return render(request, "accounts/staff_confirm_delete.html", {"profile": profile})
