from functools import wraps

from django.contrib import messages
from django.shortcuts import redirect


def get_staff_profile(user):
    return getattr(user, "staff_profile", None)


def staff_required(view_func):
    """Any logged-in staff member (has a StaffProfile)."""

    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect("accounts:login")
        if not request.user.is_superuser and get_staff_profile(request.user) is None:
            messages.error(request, "Your account is not set up as staff.")
            return redirect("accounts:login")
        return view_func(request, *args, **kwargs)

    return wrapper


def manager_required(view_func):
    """Managers and admins only."""

    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect("accounts:login")
        profile = get_staff_profile(request.user)
        if not request.user.is_superuser and (profile is None or not profile.is_manager_or_admin):
            messages.error(request, "You need manager or admin access for that.")
            return redirect("dashboard:home")
        return view_func(request, *args, **kwargs)

    return wrapper


def admin_required(view_func):
    """Admins only."""

    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect("accounts:login")
        profile = get_staff_profile(request.user)
        if not request.user.is_superuser and (profile is None or not profile.is_admin):
            messages.error(request, "You need admin access for that.")
            return redirect("dashboard:home")
        return view_func(request, *args, **kwargs)

    return wrapper
