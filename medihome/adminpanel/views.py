from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Sum, Count
from accounts.decorators import admin_required
from accounts.models import User
from diagnostics.models import DiagnosticianProfile, DiagnosticTest, Booking, SymptomTestMapping, Symptom
from hospitals.models import HospitalProfile, Doctor, Department, Appointment
from payments.models import SystemSettings, Payment, Coupon, Offer
from notifications.models import Notification

@admin_required
def dashboard_view(request):
    total_users = User.objects.count()
    patient_count = User.objects.filter(role=User.Role.PATIENT).count()
    lab_count = DiagnosticianProfile.objects.count()
    hospital_count = HospitalProfile.objects.count()

    total_bookings = Booking.objects.count()
    total_op_appts = Appointment.objects.count()

    diag_revenue = Booking.objects.aggregate(Sum('grand_total'))['grand_total__sum'] or 0
    hospital_revenue = Appointment.objects.aggregate(Sum('consultation_fee'))['consultation_fee__sum'] or 0
    total_revenue = float(diag_revenue) + float(hospital_revenue)

    recent_users = User.objects.order_by('-created_at')[:5]
    recent_bookings = Booking.objects.order_by('-created_at')[:5]

    return render(request, 'adminpanel/dashboard.html', {
        'total_users': total_users,
        'patient_count': patient_count,
        'lab_count': lab_count,
        'hospital_count': hospital_count,
        'total_bookings': total_bookings,
        'total_op_appts': total_op_appts,
        'total_revenue': round(total_revenue, 2),
        'recent_users': recent_users,
        'recent_bookings': recent_bookings,
        'system_settings': SystemSettings.get_settings()
    })


@admin_required
def manage_users_view(request):
    users = User.objects.order_by('-created_at')
    return render(request, 'adminpanel/users.html', {'users_list': users})


@admin_required
def manage_labs_view(request):
    labs = DiagnosticianProfile.objects.select_related('user').all()
    return render(request, 'adminpanel/labs.html', {'labs_list': labs})


@admin_required
def toggle_lab_approval_view(request, lab_id):
    lab = get_object_or_404(DiagnosticianProfile, id=lab_id)
    lab.is_approved_by_admin = not lab.is_approved_by_admin
    lab.save()

    status_str = "Approved" if lab.is_approved_by_admin else "Approval Revoked"
    Notification.objects.create(
        user=lab.user,
        title=f"Diagnostician Status Update: {status_str}",
        message=f"Administrator has set your laboratory approval status to: {status_str}.",
        link="/diagnostics/dashboard/"
    )

    messages.success(request, f"Lab '{lab.lab_name}' status updated to {status_str}.")
    return redirect('adminpanel:manage_labs')


@admin_required
def manage_hospitals_view(request):
    hospitals = HospitalProfile.objects.select_related('user').all()
    return render(request, 'adminpanel/hospitals.html', {'hospitals_list': hospitals})


@admin_required
def toggle_hospital_approval_view(request, hospital_id):
    hospital = get_object_or_404(HospitalProfile, id=hospital_id)
    hospital.is_approved_by_admin = not hospital.is_approved_by_admin
    hospital.save()

    status_str = "Approved" if hospital.is_approved_by_admin else "Approval Revoked"
    Notification.objects.create(
        user=hospital.user,
        title=f"Hospital Status Update: {status_str}",
        message=f"Administrator has set your hospital approval status to: {status_str}.",
        link="/hospitals/dashboard/"
    )

    messages.success(request, f"Hospital '{hospital.hospital_name}' status updated to {status_str}.")
    return redirect('adminpanel:manage_hospitals')


@admin_required
def manage_system_settings_view(request):
    settings_obj = SystemSettings.get_settings()
    if request.method == 'POST':
        gst = request.POST.get('gst_percentage', '18.0').strip()
        pf = request.POST.get('platform_fee', '50.0').strip()
        hc = request.POST.get('home_collection_charge', '150.0').strip()
        email = request.POST.get('support_email', '').strip()
        phone = request.POST.get('support_phone', '').strip()

        settings_obj.gst_percentage = float(gst)
        settings_obj.platform_fee = float(pf)
        settings_obj.home_collection_charge = float(hc)
        settings_obj.support_email = email
        settings_obj.support_phone = phone
        settings_obj.save()

        messages.success(request, "System Settings updated dynamically across entire application!")
        return redirect('adminpanel:manage_system_settings')

    return render(request, 'adminpanel/system_settings.html', {'settings_obj': settings_obj})


@admin_required
def manage_symptom_mappings_view(request):
    mappings = SymptomTestMapping.objects.select_related('symptom').all()
    symptoms = Symptom.objects.all()

    if request.method == 'POST':
        sym_id = request.POST.get('symptom_id')
        test_name = request.POST.get('test_name', '').strip()
        weight = int(request.POST.get('frequency_weight', 3))

        symptom = get_object_or_404(Symptom, id=sym_id)
        SymptomTestMapping.objects.create(
            symptom=symptom,
            test_name=test_name,
            frequency_weight=weight
        )
        messages.success(request, f"Mapping '{symptom.name} -> {test_name}' created.")
        return redirect('adminpanel:manage_symptom_mappings')

    return render(request, 'adminpanel/symptom_mappings.html', {
        'mappings': mappings,
        'symptoms': symptoms
    })
