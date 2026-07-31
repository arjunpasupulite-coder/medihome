import uuid
from datetime import date, datetime, timedelta
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db import transaction
from django.db.models import Sum, Count
from django.contrib.auth.decorators import login_required
from accounts.decorators import hospital_required, patient_required
from .models import HospitalProfile, Department, Doctor, Appointment
from .forms import DepartmentForm, DoctorForm
from payments.models import Payment, Invoice
from notifications.models import Notification

DOCTOR_RECOMMENDATION_MAPPINGS = [
    {'symptom': 'Fever / Viral Cold / Cough', 'specialty': 'General Physician', 'dept': 'General Medicine', 'icon': '🤒'},
    {'symptom': 'Chest Pain / Palpitations / High BP', 'specialty': 'Cardiologist', 'dept': 'Cardiology', 'icon': '🫀'},
    {'symptom': 'Skin Rash / Allergy / Acne', 'specialty': 'Dermatologist', 'dept': 'Dermatology', 'icon': '🧴'},
    {'symptom': 'Ear Infection / Nasal Congestion / Throat Pain', 'specialty': 'ENT Specialist', 'dept': 'ENT', 'icon': '👂'},
    {'symptom': 'Joint Pain / Fracture / Back Ache', 'specialty': 'Orthopedic Surgeon', 'dept': 'Orthopedics', 'icon': '🦴'},
    {'symptom': 'Severe Headache / Seizures / Migraine', 'specialty': 'Neurologist', 'dept': 'Neurology', 'icon': '🧠'},
    {'symptom': 'Pregnancy / Women Health / Menstrual Care', 'specialty': 'Gynecologist', 'dept': 'Gynecology', 'icon': '👩‍⚕️'},
    {'symptom': 'Child Illness / Pediatric Care / Vaccination', 'specialty': 'Pediatrician', 'dept': 'Pediatrics', 'icon': '👶'},
    {'symptom': 'Toothache / Gum Infection / Cavity', 'specialty': 'Dentist', 'dept': 'Dental', 'icon': '🦷'},
]

@hospital_required
def dashboard_view(request):
    hospital_profile = getattr(request.user, 'hospital_profile', None)
    departments = Department.objects.filter(hospital=hospital_profile)
    doctors = Doctor.objects.filter(hospital=hospital_profile)
    appointments = Appointment.objects.filter(hospital=hospital_profile)

    today = date.today()
    daily_rev = appointments.filter(created_at__date=today).aggregate(Sum('consultation_fee'))['consultation_fee__sum'] or 0
    total_rev = appointments.aggregate(Sum('consultation_fee'))['consultation_fee__sum'] or 0

    return render(request, 'hospitals/dashboard.html', {
        'hospital_profile': hospital_profile,
        'departments_count': departments.count(),
        'doctors_count': doctors.count(),
        'appointments_count': appointments.count(),
        'daily_revenue': daily_rev,
        'total_revenue': total_rev,
        'appointments': appointments[:10]
    })


@patient_required
def op_booking_hospitals_view(request):
    hospitals = HospitalProfile.objects.filter(is_approved_by_admin=True)
    return render(request, 'hospitals/op_booking_hospitals.html', {'hospitals': hospitals})


@patient_required
def op_booking_departments_view(request, hospital_id):
    hospital = get_object_or_404(HospitalProfile, id=hospital_id, is_approved_by_admin=True)
    departments = Department.objects.filter(hospital=hospital)
    return render(request, 'hospitals/op_booking_departments.html', {'hospital': hospital, 'departments': departments})


@patient_required
def op_booking_doctors_view(request, department_id):
    department = get_object_or_404(Department, id=department_id)
    doctors = Doctor.objects.filter(department=department)
    return render(request, 'hospitals/op_booking_doctors.html', {'department': department, 'hospital': department.hospital, 'doctors': doctors})


@patient_required
def op_booking_slots_view(request, doctor_id):
    doctor = get_object_or_404(Doctor, id=doctor_id)
    selected_date_str = request.GET.get('date', str(date.today()))

    try:
        target_date = datetime.strptime(selected_date_str, "%Y-%m-%d").date()
    except ValueError:
        target_date = date.today()

    all_slots = doctor.get_available_slots(target_date)
    booked_slots = list(Appointment.objects.filter(
        doctor=doctor,
        appointment_date=target_date,
        status__in=[Appointment.Status.CONFIRMED, Appointment.Status.PENDING]
    ).values_list('appointment_time', flat=True))

    available_slots = [slot for slot in all_slots if slot not in booked_slots]

    return render(request, 'hospitals/op_booking_slots.html', {
        'doctor': doctor,
        'target_date': target_date,
        'all_slots': all_slots,
        'booked_slots': booked_slots,
        'available_slots': available_slots
    })


@patient_required
@transaction.atomic
def op_booking_confirm_view(request, doctor_id):
    doctor = get_object_or_404(Doctor, id=doctor_id)

    if request.method != 'POST':
        return redirect('hospitals:op_booking_slots', doctor_id=doctor.id)

    appt_date_str = request.POST.get('appointment_date', '').strip()
    appt_time = request.POST.get('appointment_time', '').strip()
    reason = request.POST.get('symptom_reason', '').strip()
    payment_method = request.POST.get('payment_method', 'UPI').strip()

    try:
        appt_date = datetime.strptime(appt_date_str, "%Y-%m-%d").date()
    except ValueError:
        messages.error(request, "Invalid date selection.")
        return redirect('hospitals:op_booking_slots', doctor_id=doctor.id)

    double_booked = Appointment.objects.filter(
        doctor=doctor,
        appointment_date=appt_date,
        appointment_time=appt_time,
        status__in=[Appointment.Status.CONFIRMED, Appointment.Status.PENDING]
    ).exists()

    if double_booked:
        messages.error(request, f"Time slot {appt_time} on {appt_date_str} for Dr. {doctor.name} has just been booked. Please select an alternate slot.")
        return redirect('hospitals:op_booking_slots', doctor_id=doctor.id)

    appt_num = f"OP-{uuid.uuid4().hex[:8].upper()}"

    appointment = Appointment.objects.create(
        appointment_number=appt_num,
        patient=request.user,
        hospital=doctor.hospital,
        doctor=doctor,
        appointment_date=appt_date,
        appointment_time=appt_time,
        symptom_reason=reason,
        status=Appointment.Status.CONFIRMED,
        consultation_fee=doctor.consultation_fee,
        payment_status=Appointment.PaymentStatus.PAID
    )

    tx_id = f"TXN-OP-{uuid.uuid4().hex[:8].upper()}"
    payment = Payment.objects.create(
        user=request.user,
        booking_type=Payment.BookingType.HOSPITAL_OP,
        reference_id=appt_num,
        amount=doctor.consultation_fee,
        payment_method=payment_method,
        status=Payment.Status.SUCCESS,
        transaction_id=tx_id
    )

    Invoice.objects.create(
        payment=payment,
        invoice_number=f"INV-OP-{uuid.uuid4().hex[:8].upper()}",
        line_items_json=f'{{"appointment_number": "{appt_num}", "doctor": "{doctor.name}", "fee": {doctor.consultation_fee}}}'
    )

    Notification.objects.create(
        user=request.user,
        title="OP Consultation Confirmed!",
        message=f"Appointment #{appt_num} with Dr. {doctor.name} confirmed for {appt_date_str} at {appt_time}.",
        link="/hospitals/appointments/"
    )

    messages.success(request, f"OP Consultation #{appt_num} confirmed with Dr. {doctor.name}!")
    return redirect('hospitals:appointment_list')


@login_required
def doctor_recommendations_view(request):
    selected_mapping = None
    recommended_doctors = []

    symptom_key = request.GET.get('symptom', '').strip()

    if symptom_key:
        for m in DOCTOR_RECOMMENDATION_MAPPINGS:
            if m['symptom'] == symptom_key or m['dept'].lower() in symptom_key.lower():
                selected_mapping = m
                recommended_doctors = Doctor.objects.filter(
                    department__name__iexact=m['dept'],
                    hospital__is_approved_by_admin=True
                ).select_related('hospital', 'department')
                break

    return render(request, 'hospitals/doctor_recommendations.html', {
        'mappings': DOCTOR_RECOMMENDATION_MAPPINGS,
        'selected_mapping': selected_mapping,
        'recommended_doctors': recommended_doctors,
        'symptom_key': symptom_key
    })


@login_required
def appointment_list_view(request):
    if request.user.is_patient():
        appointments = Appointment.objects.filter(patient=request.user).select_related('hospital', 'doctor', 'doctor__department')
    elif request.user.is_hospital():
        hospital_profile = getattr(request.user, 'hospital_profile', None)
        appointments = Appointment.objects.filter(hospital=hospital_profile).select_related('patient', 'doctor', 'doctor__department')
    else:
        appointments = Appointment.objects.all()[:20]

    return render(request, 'hospitals/appointment_list.html', {'appointments': appointments})


@patient_required
def cancel_appointment_view(request, appt_id):
    appointment = get_object_or_404(Appointment, id=appt_id, patient=request.user)
    if appointment.status in [Appointment.Status.CONFIRMED, Appointment.Status.PENDING]:
        appointment.status = Appointment.Status.CANCELLED
        appointment.payment_status = Appointment.PaymentStatus.REFUNDED
        appointment.save()

        Notification.objects.create(
            user=appointment.hospital.user,
            title="OP Appointment Cancelled",
            message=f"Appointment #{appointment.appointment_number} was cancelled by patient {request.user.username}.",
            link="/hospitals/appointments/"
        )

        messages.info(request, f"Appointment #{appointment.appointment_number} cancelled successfully. Fee refund initiated.")
    else:
        messages.warning(request, "This appointment cannot be cancelled.")

    return redirect('hospitals:appointment_list')


# Department CRUD
@hospital_required
def department_list_view(request):
    hospital_profile = getattr(request.user, 'hospital_profile', None)
    departments = Department.objects.filter(hospital=hospital_profile)
    return render(request, 'hospitals/department_list.html', {'departments': departments})


@hospital_required
def department_add_view(request):
    hospital_profile = getattr(request.user, 'hospital_profile', None)
    if request.method == 'POST':
        form = DepartmentForm(request.POST)
        if form.is_valid():
            dept = form.save(commit=False)
            dept.hospital = hospital_profile
            dept.save()
            messages.success(request, f"Department '{dept.name}' added.")
            return redirect('hospitals:department_list')
    else:
        form = DepartmentForm()

    return render(request, 'hospitals/department_form.html', {'form': form, 'title': 'Add Department'})


@hospital_required
def department_edit_view(request, dept_id):
    hospital_profile = getattr(request.user, 'hospital_profile', None)
    dept = get_object_or_404(Department, id=dept_id, hospital=hospital_profile)
    if request.method == 'POST':
        form = DepartmentForm(request.POST, instance=dept)
        if form.is_valid():
            form.save()
            messages.success(request, f"Department '{dept.name}' updated.")
            return redirect('hospitals:department_list')
    else:
        form = DepartmentForm(instance=dept)

    return render(request, 'hospitals/department_form.html', {'form': form, 'dept': dept, 'title': 'Edit Department'})


@hospital_required
def department_delete_view(request, dept_id):
    hospital_profile = getattr(request.user, 'hospital_profile', None)
    dept = get_object_or_404(Department, id=dept_id, hospital=hospital_profile)
    name = dept.name
    dept.delete()
    messages.info(request, f"Department '{name}' deleted.")
    return redirect('hospitals:department_list')


# Doctor CRUD
@hospital_required
def doctor_list_view(request):
    hospital_profile = getattr(request.user, 'hospital_profile', None)
    doctors = Doctor.objects.filter(hospital=hospital_profile).select_related('department')
    return render(request, 'hospitals/doctor_list.html', {'doctors': doctors})


@hospital_required
def doctor_add_view(request):
    hospital_profile = getattr(request.user, 'hospital_profile', None)
    if request.method == 'POST':
        form = DoctorForm(request.POST, request.FILES)
        if form.is_valid():
            doc = form.save(commit=False)
            doc.hospital = hospital_profile
            doc.save()
            messages.success(request, f"Dr. '{doc.name}' added successfully.")
            return redirect('hospitals:doctor_list')
    else:
        form = DoctorForm()
        form.fields['department'].queryset = Department.objects.filter(hospital=hospital_profile)

    return render(request, 'hospitals/doctor_form.html', {'form': form, 'title': 'Add Doctor'})


@hospital_required
def doctor_edit_view(request, doc_id):
    hospital_profile = getattr(request.user, 'hospital_profile', None)
    doc = get_object_or_404(Doctor, id=doc_id, hospital=hospital_profile)
    if request.method == 'POST':
        form = DoctorForm(request.POST, request.FILES, instance=doc)
        if form.is_valid():
            form.save()
            messages.success(request, f"Dr. '{doc.name}' details updated.")
            return redirect('hospitals:doctor_list')
    else:
        form = DoctorForm(instance=doc)
        form.fields['department'].queryset = Department.objects.filter(hospital=hospital_profile)

    return render(request, 'hospitals/doctor_form.html', {'form': form, 'doc': doc, 'title': 'Edit Doctor Details'})


@hospital_required
def doctor_delete_view(request, doc_id):
    hospital_profile = getattr(request.user, 'hospital_profile', None)
    doc = get_object_or_404(Doctor, id=doc_id, hospital=hospital_profile)
    name = doc.name
    doc.delete()
    messages.info(request, f"Dr. '{name}' record deleted.")
    return redirect('hospitals:doctor_list')


# Hospital Revenue Analytics
@hospital_required
def hospital_revenue_view(request):
    hospital_profile = getattr(request.user, 'hospital_profile', None)
    appointments = Appointment.objects.filter(hospital=hospital_profile)

    today = date.today()
    start_week = today - timedelta(days=today.weekday())
    start_month = today.replace(day=1)

    daily_rev = appointments.filter(created_at__date=today).aggregate(Sum('consultation_fee'))['consultation_fee__sum'] or 0
    weekly_rev = appointments.filter(created_at__date__gte=start_week).aggregate(Sum('consultation_fee'))['consultation_fee__sum'] or 0
    monthly_rev = appointments.filter(created_at__date__gte=start_month).aggregate(Sum('consultation_fee'))['consultation_fee__sum'] or 0
    total_rev = appointments.aggregate(Sum('consultation_fee'))['consultation_fee__sum'] or 0

    popular_doctors = appointments.values('doctor__name', 'doctor__department__name').annotate(
        op_count=Count('id'),
        total_revenue=Sum('consultation_fee')
    ).order_by('-op_count')[:5]

    return render(request, 'hospitals/revenue.html', {
        'daily_revenue': daily_rev,
        'weekly_revenue': weekly_rev,
        'monthly_revenue': monthly_rev,
        'total_revenue': total_rev,
        'popular_doctors': popular_doctors,
        'total_appointments': appointments.count()
    })
