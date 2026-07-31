from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate, update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction

from .models import User, ActivityLog
from .forms import (
    PatientRegistrationForm, DiagnosticianRegistrationForm,
    HospitalRegistrationForm, UserProfileUpdateForm
)
from patients.models import PatientProfile
from diagnostics.models import DiagnosticianProfile
from hospitals.models import HospitalProfile

def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR', '127.0.0.1')

def log_user_activity(user, action, request, details=""):
    ActivityLog.objects.create(
        user=user if user and user.is_authenticated else None,
        action=action,
        ip_address=get_client_ip(request),
        details=details
    )


def login_patient_view(request):
    if request.user.is_authenticated:
        return redirect('patients:dashboard')

    if request.method == 'POST':
        u_name = request.POST.get('username', '').strip()
        p_word = request.POST.get('password', '').strip()
        
        user = authenticate(request, username=u_name, password=p_word)
        if user is not None:
            if not user.is_patient() and not user.is_superuser:
                messages.error(request, "Invalid account role. Please use the appropriate login portal.")
                return redirect('accounts:login_patient')
            
            login(request, user)
            log_user_activity(user, "Patient Logged In", request, f"User {user.username} logged into Patient Portal")
            messages.success(request, f"Welcome back, {user.get_full_name() or user.username}!")
            return redirect('patients:dashboard')
        else:
            messages.error(request, "Invalid username or password credentials.")
            log_user_activity(None, "Failed Patient Login Attempt", request, f"Attempted username: {u_name}")

    return render(request, 'accounts/login.html', {'role_type': 'Patient', 'role_code': 'PATIENT'})


def login_diagnostician_view(request):
    if request.user.is_authenticated:
        return redirect('diagnostics:dashboard')

    if request.method == 'POST':
        u_name = request.POST.get('username', '').strip()
        p_word = request.POST.get('password', '').strip()

        user = authenticate(request, username=u_name, password=p_word)
        if user is not None:
            if not user.is_diagnostician() and not user.is_superuser:
                messages.error(request, "Invalid account role. Please use your Diagnostician portal.")
                return redirect('accounts:login_diagnostician')
            
            # Check Admin Approval requirement for Diagnostician
            if hasattr(user, 'diagnostician_profile') and not user.diagnostician_profile.is_approved_by_admin:
                messages.warning(request, "Your Diagnostician Laboratory registration is pending Admin Approval. Please await admin review.")
                return redirect('accounts:login_diagnostician')

            login(request, user)
            log_user_activity(user, "Diagnostician Logged In", request, f"Diagnostician {user.username} logged in")
            messages.success(request, f"Welcome back to Laboratory Desk, {user.username}!")
            return redirect('diagnostics:dashboard')
        else:
            messages.error(request, "Invalid lab login credentials.")
            log_user_activity(None, "Failed Diagnostician Login Attempt", request, f"Attempted username: {u_name}")

    return render(request, 'accounts/login.html', {'role_type': 'Diagnostician', 'role_code': 'DIAGNOSTICIAN'})


def login_hospital_view(request):
    if request.user.is_authenticated:
        return redirect('hospitals:dashboard')

    if request.method == 'POST':
        u_name = request.POST.get('username', '').strip()
        p_word = request.POST.get('password', '').strip()

        user = authenticate(request, username=u_name, password=p_word)
        if user is not None:
            if not user.is_hospital() and not user.is_superuser:
                messages.error(request, "Invalid account role. Please use the Hospital portal.")
                return redirect('accounts:login_hospital')

            # Check Admin Approval requirement for Hospital
            if hasattr(user, 'hospital_profile') and not user.hospital_profile.is_approved_by_admin:
                messages.warning(request, "Your Hospital registration is pending Admin Approval. Access will be unlocked once approved.")
                return redirect('accounts:login_hospital')

            login(request, user)
            log_user_activity(user, "Hospital Logged In", request, f"Hospital {user.username} logged in")
            messages.success(request, f"Welcome to Hospital OPD Desk, {user.username}!")
            return redirect('hospitals:dashboard')
        else:
            messages.error(request, "Invalid hospital login credentials.")
            log_user_activity(None, "Failed Hospital Login Attempt", request, f"Attempted username: {u_name}")

    return render(request, 'accounts/login.html', {'role_type': 'Hospital', 'role_code': 'HOSPITAL'})


@transaction.atomic
def register_patient_view(request):
    if request.method == 'POST':
        form = PatientRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.role = User.Role.PATIENT
            user.set_password(form.cleaned_data['password'])
            user.save()

            PatientProfile.objects.create(
                user=user,
                blood_group=form.cleaned_data['blood_group'],
                dob=form.cleaned_data['dob'],
                gender=form.cleaned_data['gender'],
                emergency_contact=form.cleaned_data['emergency_contact'],
                medical_history=form.cleaned_data.get('medical_history', '')
            )

            log_user_activity(user, "Patient Account Registered", request, f"Registered patient {user.username}")
            messages.success(request, "Patient Registration Successful! Please log in with your credentials.")
            return redirect('accounts:login_patient')
        else:
            messages.error(request, "Registration failed. Please correct the validation errors below.")
    else:
        form = PatientRegistrationForm()

    return render(request, 'accounts/register_patient.html', {'form': form})


@transaction.atomic
def register_diagnostician_view(request):
    if request.method == 'POST':
        form = DiagnosticianRegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save(commit=False)
            user.role = User.Role.DIAGNOSTICIAN
            user.latitude = form.cleaned_data.get('latitude')
            user.longitude = form.cleaned_data.get('longitude')
            user.set_password(form.cleaned_data['password'])
            user.save()

            DiagnosticianProfile.objects.create(
                user=user,
                lab_name=form.cleaned_data['lab_name'],
                owner_name=form.cleaned_data['owner_name'],
                license_number=form.cleaned_data['license_number'],
                gst_number=form.cleaned_data['gst_number'],
                nabl_accredited=form.cleaned_data.get('nabl_accredited', False),
                is_home_collection_available=form.cleaned_data.get('is_home_collection_available', True),
                working_hours=form.cleaned_data.get('working_hours', '08:00 AM - 08:00 PM'),
                address=user.address or form.cleaned_data.get('address', ''),
                latitude=user.latitude,
                longitude=user.longitude,
                logo=form.cleaned_data.get('logo'),
                is_approved_by_admin=False  # Requires explicit Admin approval
            )

            log_user_activity(user, "Diagnostician Lab Registered", request, f"Registered lab {form.cleaned_data['lab_name']} (Pending Approval)")
            messages.success(request, "Diagnostician Laboratory submitted successfully! Registration is pending Admin Approval.")
            return redirect('accounts:login_diagnostician')
        else:
            messages.error(request, "Lab registration failed. Please review form inputs.")
    else:
        form = DiagnosticianRegistrationForm()

    return render(request, 'accounts/register_diagnostician.html', {'form': form})


@transaction.atomic
def register_hospital_view(request):
    if request.method == 'POST':
        form = HospitalRegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save(commit=False)
            user.role = User.Role.HOSPITAL
            user.latitude = form.cleaned_data.get('latitude')
            user.longitude = form.cleaned_data.get('longitude')
            user.set_password(form.cleaned_data['password'])
            user.save()

            HospitalProfile.objects.create(
                user=user,
                hospital_name=form.cleaned_data['hospital_name'],
                license_number=form.cleaned_data['license_number'],
                gst_number=form.cleaned_data['gst_number'],
                emergency_contact=form.cleaned_data['emergency_contact'],
                working_hours=form.cleaned_data.get('working_hours', '24/7 OPD & Emergency'),
                address=user.address or form.cleaned_data.get('address', ''),
                latitude=user.latitude,
                longitude=user.longitude,
                logo=form.cleaned_data.get('logo'),
                is_approved_by_admin=False  # Requires explicit Admin approval
            )

            log_user_activity(user, "Hospital Registered", request, f"Registered hospital {form.cleaned_data['hospital_name']} (Pending Approval)")
            messages.success(request, "Hospital account created successfully! Submitted for Admin Approval.")
            return redirect('accounts:login_hospital')
        else:
            messages.error(request, "Hospital registration failed. Please review form fields.")
    else:
        form = HospitalRegistrationForm()

    return render(request, 'accounts/register_hospital.html', {'form': form})


def logout_view(request):
    if request.user.is_authenticated:
        log_user_activity(request.user, "Logged Out", request, f"User {request.user.username} logged out")
    logout(request)
    messages.info(request, "You have been logged out safely.")
    return redirect('landing')


@login_required
def profile_view(request):
    user = request.user
    if request.method == 'POST':
        form = UserProfileUpdateForm(request.POST, request.FILES, instance=user)
        if form.is_valid():
            form.save()
            
            # Synchronize profile address & coordinates if present
            if hasattr(user, 'diagnostician_profile'):
                user.diagnostician_profile.address = user.address
                user.diagnostician_profile.latitude = user.latitude
                user.diagnostician_profile.longitude = user.longitude
                user.diagnostician_profile.save()
            elif hasattr(user, 'hospital_profile'):
                user.hospital_profile.address = user.address
                user.hospital_profile.latitude = user.latitude
                user.hospital_profile.longitude = user.longitude
                user.hospital_profile.save()

            log_user_activity(user, "Profile Updated", request, "User updated profile information")
            messages.success(request, "Profile details updated successfully.")
            return redirect('accounts:profile')
    else:
        form = UserProfileUpdateForm(instance=user)

    return render(request, 'accounts/profile.html', {'form': form, 'user_obj': user})


@login_required
def change_password_view(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            log_user_activity(user, "Password Changed", request, "User updated password")
            messages.success(request, "Your password was updated successfully!")
            return redirect('accounts:profile')
        else:
            messages.error(request, "Password update failed. Please check form errors.")
    else:
        form = PasswordChangeForm(request.user)

    return render(request, 'accounts/change_password.html', {'form': form})


def forgot_password_view(request):
    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        user_matches = User.objects.filter(email__iexact=email)
        if user_matches.exists():
            log_user_activity(user_matches.first(), "Password Reset Requested", request, f"Email: {email}")
            messages.success(request, f"Password reset instructions have been generated for {email}. (Simulation: Instructions sent).")
        else:
            messages.error(request, f"No account found matching email address {email}.")
    
    return render(request, 'accounts/forgot_password.html')
