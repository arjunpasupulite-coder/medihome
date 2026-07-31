from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages
from django.core.exceptions import PermissionDenied

def patient_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.warning(request, "Please log in as a Patient to access this page.")
            return redirect('accounts:login_patient')
        if not request.user.is_patient():
            messages.error(request, "Access denied. Patient privileges required.")
            return redirect('landing')
        return view_func(request, *args, **kwargs)
    return _wrapped_view

def diagnostician_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.warning(request, "Please log in as a Diagnostician to access this page.")
            return redirect('accounts:login_diagnostician')
        if not request.user.is_diagnostician():
            messages.error(request, "Access denied. Diagnostician lab privileges required.")
            return redirect('landing')
        return view_func(request, *args, **kwargs)
    return _wrapped_view

def hospital_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.warning(request, "Please log in as a Hospital to access this page.")
            return redirect('accounts:login_hospital')
        if not request.user.is_hospital():
            messages.error(request, "Access denied. Hospital privileges required.")
            return redirect('landing')
        return view_func(request, *args, **kwargs)
    return _wrapped_view

def admin_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.warning(request, "Administrator login required.")
            return redirect('accounts:login_patient')
        if not request.user.is_admin_role():
            messages.error(request, "Access denied. Admin privileges required.")
            return redirect('landing')
        return view_func(request, *args, **kwargs)
    return _wrapped_view
