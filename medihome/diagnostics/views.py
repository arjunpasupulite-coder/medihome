from datetime import date, timedelta
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Sum, Count
from accounts.decorators import diagnostician_required
from .models import DiagnosticianProfile, Booking, BookingStatusHistory, Technician, DiagnosticTest, BookingItem
from .forms import DiagnosticTestForm, TechnicianForm
from notifications.models import Notification

@diagnostician_required
def dashboard_view(request):
    lab_profile = getattr(request.user, 'diagnostician_profile', None)
    if not lab_profile:
        messages.error(request, "Lab profile not found.")
        return redirect('landing')

    bookings = Booking.objects.filter(diagnostician=lab_profile)
    tests = DiagnosticTest.objects.filter(lab=lab_profile)
    technicians = Technician.objects.filter(lab=lab_profile)

    today = date.today()
    daily_rev = bookings.filter(created_at__date=today).aggregate(Sum('grand_total'))['grand_total__sum'] or 0
    total_rev = bookings.aggregate(Sum('grand_total'))['grand_total__sum'] or 0

    return render(request, 'diagnostics/dashboard.html', {
        'lab_profile': lab_profile,
        'bookings': bookings[:10],
        'tests_count': tests.count(),
        'bookings_count': bookings.count(),
        'technicians_count': technicians.count(),
        'daily_revenue': daily_rev,
        'total_revenue': total_rev
    })


@diagnostician_required
def booking_list_view(request):
    lab_profile = getattr(request.user, 'diagnostician_profile', None)
    bookings = Booking.objects.filter(diagnostician=lab_profile).select_related('patient', 'technician')
    technicians = Technician.objects.filter(lab=lab_profile, is_available=True)

    return render(request, 'diagnostics/booking_list.html', {
        'lab_profile': lab_profile,
        'bookings': bookings,
        'technicians': technicians
    })


@diagnostician_required
def update_booking_status_view(request, booking_id):
    if request.method != 'POST':
        return redirect('diagnostics:booking_list')

    lab_profile = getattr(request.user, 'diagnostician_profile', None)
    booking = get_object_or_404(Booking, id=booking_id, diagnostician=lab_profile)
    
    new_status = request.POST.get('status', '').strip()
    technician_id = request.POST.get('technician_id', '').strip()
    notes = request.POST.get('notes', '').strip()

    if new_status in Booking.Status.values:
        booking.status = new_status

        if technician_id and technician_id.isdigit():
            tech = Technician.objects.filter(id=int(technician_id), lab=lab_profile).first()
            if tech:
                booking.technician = tech

        booking.save()

        BookingStatusHistory.objects.create(
            booking=booking,
            status=new_status,
            updated_by=request.user,
            notes=notes or f"Status updated to {booking.get_status_display()} by lab admin."
        )

        Notification.objects.create(
            user=booking.patient,
            title=f"Booking #{booking.booking_number} Status Updated",
            message=f"Your diagnostic booking status is now: {booking.get_status_display()}.",
            link=f"/patients/booking/{booking.id}/"
        )

        messages.success(request, f"Booking #{booking.booking_number} updated to {booking.get_status_display()}.")
    else:
        messages.error(request, "Invalid status choice.")

    return redirect('diagnostics:booking_list')


# Test CRUD
@diagnostician_required
def test_list_view(request):
    lab_profile = getattr(request.user, 'diagnostician_profile', None)
    tests = DiagnosticTest.objects.filter(lab=lab_profile)
    return render(request, 'diagnostics/test_list.html', {'tests': tests})


@diagnostician_required
def test_add_view(request):
    lab_profile = getattr(request.user, 'diagnostician_profile', None)
    if request.method == 'POST':
        form = DiagnosticTestForm(request.POST)
        if form.is_valid():
            test = form.save(commit=False)
            test.lab = lab_profile
            test.save()
            messages.success(request, f"Test '{test.name}' added successfully.")
            return redirect('diagnostics:test_list')
    else:
        form = DiagnosticTestForm()

    return render(request, 'diagnostics/test_form.html', {'form': form, 'title': 'Add New Diagnostic Test'})


@diagnostician_required
def test_edit_view(request, test_id):
    lab_profile = getattr(request.user, 'diagnostician_profile', None)
    test = get_object_or_404(DiagnosticTest, id=test_id, lab=lab_profile)
    if request.method == 'POST':
        form = DiagnosticTestForm(request.POST, instance=test)
        if form.is_valid():
            form.save()
            messages.success(request, f"Test '{test.name}' updated.")
            return redirect('diagnostics:test_list')
    else:
        form = DiagnosticTestForm(instance=test)

    return render(request, 'diagnostics/test_form.html', {'form': form, 'test': test, 'title': 'Edit Diagnostic Test'})


@diagnostician_required
def test_delete_view(request, test_id):
    lab_profile = getattr(request.user, 'diagnostician_profile', None)
    test = get_object_or_404(DiagnosticTest, id=test_id, lab=lab_profile)
    name = test.name
    test.delete()
    messages.info(request, f"Test '{name}' deleted.")
    return redirect('diagnostics:test_list')


# Technician CRUD
@diagnostician_required
def technician_list_view(request):
    lab_profile = getattr(request.user, 'diagnostician_profile', None)
    technicians = Technician.objects.filter(lab=lab_profile)
    return render(request, 'diagnostics/technician_list.html', {'technicians': technicians})


@diagnostician_required
def technician_add_view(request):
    lab_profile = getattr(request.user, 'diagnostician_profile', None)
    if request.method == 'POST':
        form = TechnicianForm(request.POST)
        if form.is_valid():
            tech = form.save(commit=False)
            tech.lab = lab_profile
            tech.save()
            messages.success(request, f"Technician '{tech.name}' added.")
            return redirect('diagnostics:technician_list')
    else:
        form = TechnicianForm()

    return render(request, 'diagnostics/technician_form.html', {'form': form, 'title': 'Add Technician'})


@diagnostician_required
def technician_edit_view(request, tech_id):
    lab_profile = getattr(request.user, 'diagnostician_profile', None)
    tech = get_object_or_404(Technician, id=tech_id, lab=lab_profile)
    if request.method == 'POST':
        form = TechnicianForm(request.POST, instance=tech)
        if form.is_valid():
            form.save()
            messages.success(request, f"Technician '{tech.name}' updated.")
            return redirect('diagnostics:technician_list')
    else:
        form = TechnicianForm(instance=tech)

    return render(request, 'diagnostics/technician_form.html', {'form': form, 'tech': tech, 'title': 'Edit Technician'})


@diagnostician_required
def technician_delete_view(request, tech_id):
    lab_profile = getattr(request.user, 'diagnostician_profile', None)
    tech = get_object_or_404(Technician, id=tech_id, lab=lab_profile)
    name = tech.name
    tech.delete()
    messages.info(request, f"Technician '{name}' deleted.")
    return redirect('diagnostics:technician_list')


# Revenue Analytics
@diagnostician_required
def revenue_analytics_view(request):
    lab_profile = getattr(request.user, 'diagnostician_profile', None)
    bookings = Booking.objects.filter(diagnostician=lab_profile)

    today = date.today()
    start_week = today - timedelta(days=today.weekday())
    start_month = today.replace(day=1)

    daily_rev = bookings.filter(created_at__date=today).aggregate(Sum('grand_total'))['grand_total__sum'] or 0
    weekly_rev = bookings.filter(created_at__date__gte=start_week).aggregate(Sum('grand_total'))['grand_total__sum'] or 0
    monthly_rev = bookings.filter(created_at__date__gte=start_month).aggregate(Sum('grand_total'))['grand_total__sum'] or 0
    total_rev = bookings.aggregate(Sum('grand_total'))['grand_total__sum'] or 0

    popular_tests = BookingItem.objects.filter(
        booking__diagnostician=lab_profile
    ).values('test__name').annotate(
        order_count=Count('id'),
        total_sales=Sum('price')
    ).order_by('-order_count')[:5]

    return render(request, 'diagnostics/revenue.html', {
        'daily_revenue': daily_rev,
        'weekly_revenue': weekly_rev,
        'monthly_revenue': monthly_rev,
        'total_revenue': total_rev,
        'popular_tests': popular_tests,
        'total_orders': bookings.count()
    })
