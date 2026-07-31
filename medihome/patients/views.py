import uuid
from datetime import date, datetime, timedelta
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db import transaction
from django.db.models import Max, Avg, Q
from accounts.decorators import patient_required
from diagnostics.models import (
    DiagnosticTest, DiagnosticianProfile, Symptom,
    SymptomTestMapping, Cart, CartItem, Booking, BookingItem, BookingStatusHistory
)
from patients.models import PatientProfile, MedicineReminder, Wishlist
from payments.models import SystemSettings, Coupon, Offer, Payment, Invoice
from notifications.models import Notification

EXCLUDED_HOME_COLLECTION_TESTS = [
    'mri', 'ct scan', 'pet scan', 'ultrasound', 'x-ray', 'xray',
    'endoscopy', 'colonoscopy', 'eeg'
]

def get_cart_calculations(user, coupon_code=None):
    system_settings = SystemSettings.get_settings()
    cart, _ = Cart.objects.get_or_create(user=user)
    cart_items = CartItem.objects.filter(cart=cart).select_related('test', 'test__lab')
    
    subtotal = sum(float(item.test.price) for item in cart_items)
    
    gst_pct = float(system_settings.gst_percentage)
    gst_amount = (subtotal * gst_pct) / 100.0
    platform_fee = float(system_settings.platform_fee) if cart_items.exists() else 0.0
    
    has_home_coll = any(item.test.is_home_collection_compatible for item in cart_items)
    home_coll_fee = float(system_settings.home_collection_charge) if (cart_items.exists() and has_home_coll) else 0.0

    discount_amount = 0.0
    applied_coupon = None
    coupon_message = ""

    if coupon_code:
        try:
            coupon = Coupon.objects.get(code__iexact=coupon_code)
            is_valid, msg = coupon.is_valid(subtotal)
            if is_valid:
                discount_amount = coupon.calculate_discount(subtotal)
                applied_coupon = coupon
                coupon_message = f"Coupon '{coupon.code}' applied successfully!"
            else:
                coupon_message = msg
        except Coupon.DoesNotExist:
            coupon_message = "Invalid coupon code."

    grand_total = max(0.0, subtotal + gst_amount + platform_fee + home_coll_fee - discount_amount)

    return {
        'cart': cart,
        'cart_items': cart_items,
        'subtotal': round(subtotal, 2),
        'gst_percentage': gst_pct,
        'gst_amount': round(gst_amount, 2),
        'platform_fee': round(platform_fee, 2),
        'home_collection_fee': round(home_coll_fee, 2),
        'discount_amount': round(discount_amount, 2),
        'grand_total': round(grand_total, 2),
        'applied_coupon': applied_coupon,
        'coupon_message': coupon_message,
        'system_settings': system_settings
    }


@patient_required
def dashboard_view(request):
    cart_info = get_cart_calculations(request.user)
    patient_profile = getattr(request.user, 'patient_profile', None)
    
    today = date.today()
    all_reminders = MedicineReminder.objects.filter(patient=patient_profile) if patient_profile else []
    active_reminders = []
    
    for r in all_reminders:
        end_date = r.start_date + timedelta(days=r.duration_days)
        if r.start_date <= today <= end_date:
            active_reminders.append({
                'reminder': r,
                'is_active': True,
                'days_remaining': (end_date - today).days
            })

    bookings = Booking.objects.filter(patient=request.user)[:5]
    appointments = request.user.appointments.all()[:5]
    medical_reports = request.user.medical_reports.all()[:5]

    return render(request, 'patients/dashboard.html', {
        'user': request.user,
        'cart_count': cart_info['cart_items'].count(),
        'active_reminders': active_reminders,
        'bookings': bookings,
        'appointments': appointments,
        'reports': medical_reports,
        'today': today
    })


@patient_required
def diagnostic_search_view(request):
    query = request.GET.get('q', '').strip()
    category = request.GET.get('category', '').strip()

    tests = DiagnosticTest.objects.filter(
        is_home_collection_compatible=True,
        lab__is_approved_by_admin=True
    ).select_related('lab')

    for exc in EXCLUDED_HOME_COLLECTION_TESTS:
        tests = tests.exclude(name__icontains=exc)

    if query:
        tests = tests.filter(Q(name__icontains=query) | Q(category__icontains=query) | Q(lab__lab_name__icontains=query))

    if category:
        tests = tests.filter(category__iexact=category)

    categories = DiagnosticTest.objects.values_list('category', flat=True).distinct()

    return render(request, 'patients/diagnostic_search.html', {
        'tests': tests,
        'query': query,
        'selected_category': category,
        'categories': categories
    })


@patient_required
def test_lab_search_view(request, test_name):
    # Find all laboratories offering the specific diagnostic test name
    tests = DiagnosticTest.objects.filter(
        name__iexact=test_name,
        is_home_collection_compatible=True,
        lab__is_approved_by_admin=True
    ).select_related('lab')

    user_lat = request.user.latitude
    user_lng = request.user.longitude

    lab_test_list = []
    for t in tests:
        lab_profile = t.lab
        lab_test_list.append({
            'test': t,
            'lab': lab_profile,
            'avg_rating': lab_profile.get_average_rating(),
            'total_reviews': lab_profile.get_total_reviews(),
            'distance': lab_profile.calculate_distance(user_lat, user_lng)
        })

    return render(request, 'patients/test_lab_search.html', {
        'test_name': test_name,
        'lab_test_list': lab_test_list
    })


@patient_required
def symptom_recommendation_view(request):
    symptoms = Symptom.objects.all()
    selected_symptom_ids = [int(sid) for sid in request.GET.getlist('symptoms') if sid.isdigit()]
    
    recommendations = []
    
    if selected_symptom_ids:
        mappings = SymptomTestMapping.objects.filter(
            symptom__id__in=selected_symptom_ids
        ).values('test_name').annotate(
            max_weight=Max('frequency_weight')
        ).order_by('-max_weight')

        for item in mappings:
            tname = item['test_name']
            weight = item['max_weight']
            matching_tests = DiagnosticTest.objects.filter(
                name__icontains=tname,
                is_home_collection_compatible=True,
                lab__is_approved_by_admin=True
            ).select_related('lab')

            recommendations.append({
                'test_name': tname,
                'frequency_weight': weight,
                'stars': '★' * weight + '☆' * (5 - weight),
                'available_tests': matching_tests
            })

    disclaimer = "Recommendations are generated from predefined database mappings and should not replace professional medical advice."

    return render(request, 'patients/diagnostic_recommendation.html', {
        'symptoms': symptoms,
        'selected_symptom_ids': selected_symptom_ids,
        'recommendations': recommendations,
        'disclaimer': disclaimer
    })


@patient_required
def lab_search_view(request):
    query = request.GET.get('q', '').strip()
    min_rating = request.GET.get('rating', '')
    home_collection_only = request.GET.get('home_collection', '') == '1'

    labs = DiagnosticianProfile.objects.filter(is_approved_by_admin=True)

    if query:
        labs = labs.filter(Q(lab_name__icontains=query) | Q(address__icontains=query))

    if home_collection_only:
        labs = labs.filter(is_home_collection_available=True)

    lab_list = []
    user_lat = request.user.latitude
    user_lng = request.user.longitude

    for lab in labs:
        avg_rating = lab.get_average_rating()
        total_reviews = lab.get_total_reviews()
        distance_str = lab.calculate_distance(user_lat, user_lng)

        if min_rating and avg_rating < float(min_rating):
            continue

        lab_list.append({
            'profile': lab,
            'avg_rating': avg_rating,
            'total_reviews': total_reviews,
            'distance': distance_str,
            'test_count': lab.tests.count()
        })

    active_offers = Offer.objects.filter(is_active=True)

    return render(request, 'patients/lab_search.html', {
        'labs': lab_list,
        'query': query,
        'min_rating': min_rating,
        'home_collection_only': home_collection_only,
        'offers': active_offers
    })


@patient_required
def cart_view(request):
    coupon_code = request.GET.get('coupon_code', '').strip() or request.POST.get('coupon_code', '').strip()
    cart_data = get_cart_calculations(request.user, coupon_code=coupon_code)
    return render(request, 'patients/cart.html', cart_data)


@patient_required
def add_to_cart_view(request, test_id):
    test = get_object_or_404(DiagnosticTest, id=test_id)
    
    if not test.is_home_collection_compatible:
        messages.error(request, f"'{test.name}' requires specialized in-lab imaging equipment and cannot be added to Home Collection Cart.")
        return redirect('patients:diagnostic_search')

    cart, _ = Cart.objects.get_or_create(user=request.user)
    
    existing = CartItem.objects.filter(cart=cart, test=test).exists()
    if existing:
        messages.warning(request, f"'{test.name}' is already in your cart.")
    else:
        CartItem.objects.create(cart=cart, test=test)
        messages.success(request, f"'{test.name}' added to cart successfully.")

    return redirect('patients:cart')


@patient_required
def remove_from_cart_view(request, item_id):
    cart = get_object_or_404(Cart, user=request.user)
    cart_item = get_object_or_404(CartItem, id=item_id, cart=cart)
    test_name = cart_item.test.name
    cart_item.delete()
    messages.info(request, f"'{test_name}' removed from cart.")
    return redirect('patients:cart')


@patient_required
def clear_cart_view(request):
    cart = get_object_or_404(Cart, user=request.user)
    cart.items.all().delete()
    messages.info(request, "Your cart has been cleared.")
    return redirect('patients:cart')


@patient_required
def checkout_view(request):
    coupon_code = request.POST.get('coupon_code', '').strip() or request.GET.get('coupon_code', '').strip()
    cart_data = get_cart_calculations(request.user, coupon_code=coupon_code)

    if not cart_data['cart_items'].exists():
        messages.warning(request, "Your cart is empty. Add diagnostic tests before checking out.")
        return redirect('patients:diagnostic_search')

    return render(request, 'patients/checkout.html', cart_data)


@patient_required
@transaction.atomic
def process_booking_payment_view(request):
    if request.method != 'POST':
        return redirect('patients:cart')

    coupon_code = request.POST.get('coupon_code', '').strip()
    collection_date_str = request.POST.get('collection_date', '').strip()
    collection_time = request.POST.get('collection_time', '').strip()
    address = request.POST.get('address', '').strip()
    payment_method = request.POST.get('payment_method', 'UPI').strip()

    cart_data = get_cart_calculations(request.user, coupon_code=coupon_code)
    cart_items = cart_data['cart_items']

    if not cart_items.exists():
        messages.error(request, "Your cart is empty.")
        return redirect('patients:diagnostic_search')

    lab_tests_map = {}
    for citem in cart_items:
        lab = citem.test.lab
        if lab not in lab_tests_map:
            lab_tests_map[lab] = []
        lab_tests_map[lab].append(citem.test)

    created_bookings = []
    
    for lab, tests in lab_tests_map.items():
        b_num = f"BK-{uuid.uuid4().hex[:8].upper()}"
        lab_subtotal = sum(float(t.price) for t in tests)
        lab_gst = (lab_subtotal * cart_data['gst_percentage']) / 100.0
        lab_platform = cart_data['platform_fee'] / len(lab_tests_map)
        lab_home_coll = cart_data['home_collection_fee'] / len(lab_tests_map)
        lab_discount = cart_data['discount_amount'] / len(lab_tests_map)
        lab_grand_total = max(0.0, lab_subtotal + lab_gst + lab_platform + lab_home_coll - lab_discount)

        booking = Booking.objects.create(
            booking_number=b_num,
            patient=request.user,
            diagnostician=lab,
            total_amount=round(lab_subtotal, 2),
            gst_amount=round(lab_gst, 2),
            discount_amount=round(lab_discount, 2),
            home_collection_fee=round(lab_home_coll, 2),
            platform_fee=round(lab_platform, 2),
            grand_total=round(lab_grand_total, 2),
            status=Booking.Status.CONFIRMED,
            collection_date=collection_date_str,
            collection_time=collection_time,
            address=address
        )

        for t in tests:
            BookingItem.objects.create(booking=booking, test=t, price=t.price)

        BookingStatusHistory.objects.create(
            booking=booking,
            status=Booking.Status.CONFIRMED,
            updated_by=request.user,
            notes="Booking confirmed by patient upon payment authorization."
        )

        tx_id = f"TXN-{uuid.uuid4().hex[:10].upper()}"
        payment = Payment.objects.create(
            user=request.user,
            booking_type=Payment.BookingType.DIAGNOSTIC,
            reference_id=b_num,
            amount=booking.grand_total,
            payment_method=payment_method,
            status=Payment.Status.SUCCESS,
            transaction_id=tx_id
        )

        inv_num = f"INV-{uuid.uuid4().hex[:8].upper()}"
        Invoice.objects.create(
            payment=payment,
            invoice_number=inv_num,
            line_items_json=f'{{"booking_number": "{b_num}", "subtotal": {lab_subtotal}, "gst": {lab_gst}, "grand_total": {lab_grand_total}}}'
        )

        Notification.objects.create(
            user=request.user,
            title="Diagnostic Booking Confirmed!",
            message=f"Booking #{b_num} for {lab.lab_name} placed successfully for {collection_date_str}.",
            link=f"/patients/booking/{booking.id}/"
        )

        created_bookings.append(booking)

    cart_items.delete()

    messages.success(request, f"Order placed successfully! {len(created_bookings)} diagnostic booking(s) generated.")
    return redirect('patients:booking_detail', booking_id=created_bookings[0].id)


@patient_required
def patient_bookings_history_view(request):
    bookings = Booking.objects.filter(patient=request.user).select_related('diagnostician', 'technician')
    return render(request, 'patients/booking_history.html', {
        'bookings': bookings
    })


@patient_required
def booking_detail_view(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)
    
    if booking.patient != request.user and (not hasattr(request.user, 'diagnostician_profile') or booking.diagnostician != request.user.diagnostician_profile) and not request.user.is_admin_role():
        messages.error(request, "Unauthorized access to booking details.")
        return redirect('landing')

    status_history = booking.status_history.all()
    
    stages = [
        ('CONFIRMED', 'Booking Confirmed', '📋'),
        ('TECHNICIAN_ASSIGNED', 'Technician Assigned', '🚴'),
        ('TECHNICIAN_ON_THE_WAY', 'Technician On The Way', '🚗'),
        ('SAMPLE_COLLECTED', 'Sample Collected', '🩸'),
        ('REACHED_LABORATORY', 'Reached Laboratory', '🔬'),
        ('TESTING', 'Testing Phase', '🧪'),
        ('REPORT_UPLOADED', 'Report Uploaded', '📄'),
        ('COMPLETED', 'Completed', '✅')
    ]

    status_order = [s[0] for s in stages]
    current_index = status_order.index(booking.status) if booking.status in status_order else 0

    stage_list = []
    for idx, (code, label, icon) in enumerate(stages):
        stage_list.append({
            'code': code,
            'label': label,
            'icon': icon,
            'is_completed': idx <= current_index,
            'is_current': idx == current_index
        })

    return render(request, 'patients/booking_detail.html', {
        'booking': booking,
        'status_history': status_history,
        'stages': stage_list,
        'current_status': booking.get_status_display()
    })


@patient_required
def medicine_reminders_view(request):
    patient_profile = getattr(request.user, 'patient_profile', None)
    if not patient_profile:
        messages.error(request, "Patient profile missing.")
        return redirect('patients:dashboard')

    today = date.today()
    reminders = MedicineReminder.objects.filter(patient=patient_profile)
    
    reminder_list = []
    for r in reminders:
        end_date = r.start_date + timedelta(days=r.duration_days)
        is_expired = today > end_date
        reminder_list.append({
            'reminder': r,
            'end_date': end_date,
            'is_expired': is_expired,
            'is_active_today': r.start_date <= today <= end_date
        })

    return render(request, 'patients/medicine_reminders.html', {
        'reminders': reminder_list,
        'today': today
    })


@patient_required
def add_medicine_reminder_view(request):
    patient_profile = getattr(request.user, 'patient_profile', None)
    if request.method == 'POST':
        med_name = request.POST.get('medicine_name', '').strip()
        morning = 'morning' in request.POST
        afternoon = 'afternoon' in request.POST
        night = 'night' in request.POST
        duration = int(request.POST.get('duration_days', 7))
        start_date_str = request.POST.get('start_date', str(date.today()))
        notes = request.POST.get('notes', '').strip()

        if med_name:
            MedicineReminder.objects.create(
                patient=patient_profile,
                medicine_name=med_name,
                morning=morning,
                afternoon=afternoon,
                night=night,
                duration_days=duration,
                start_date=start_date_str,
                notes=notes
            )
            messages.success(request, f"Medicine reminder for '{med_name}' added successfully!")
        else:
            messages.error(request, "Medicine name is required.")

    return redirect('patients:medicine_reminders')


@patient_required
def delete_medicine_reminder_view(request, reminder_id):
    patient_profile = getattr(request.user, 'patient_profile', None)
    reminder = get_object_or_404(MedicineReminder, id=reminder_id, patient=patient_profile)
    name = reminder.medicine_name
    reminder.delete()
    messages.info(request, f"Reminder for '{name}' deleted.")
    return redirect('patients:medicine_reminders')
