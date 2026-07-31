from datetime import date, timedelta
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction

from accounts.models import User, ActivityLog
from patients.models import PatientProfile, MedicineReminder, Wishlist
from diagnostics.models import (
    DiagnosticianProfile, DiagnosticTest, Symptom, SymptomTestMapping,
    Technician, Booking, BookingItem, BookingStatusHistory
)
from hospitals.models import HospitalProfile, Department, Doctor, Appointment
from payments.models import SystemSettings, Coupon, Offer, Payment, Invoice, FAQ, ContactMessage
from reports.models import MedicalReport
from adminpanel.models import Review

class Command(BaseCommand):
    help = "Seeds database with realistic production-quality sample data for MediHome."

    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write("Starting MediHome database seeding...")

        # 1. System Settings
        sys_settings = SystemSettings.get_settings()
        sys_settings.gst_percentage = 18.00
        sys_settings.platform_fee = 50.00
        sys_settings.home_collection_charge = 150.00
        sys_settings.support_email = "support@medihome.com"
        sys_settings.support_phone = "+91 1800-123-4567"
        sys_settings.save()
        self.stdout.write("[OK] SystemSettings initialized (GST 18%, Platform Fee Rs.50, Home Coll Fee Rs.150)")

        # 2. Demo Users
        admin_user, _ = User.objects.get_or_create(
            username='admin_demo',
            defaults={
                'email': 'admin@medihome.com',
                'role': User.Role.ADMIN,
                'is_staff': True,
                'is_superuser': True,
                'phone_number': '+91 9876543210',
                'address': 'MediHome HQ, Healthcare Towers, Bengaluru'
            }
        )
        admin_user.set_password('password123')
        admin_user.save()

        patient_user, _ = User.objects.get_or_create(
            username='patient_demo',
            defaults={
                'email': 'patient@example.com',
                'role': User.Role.PATIENT,
                'first_name': 'Rahul',
                'last_name': 'Sharma',
                'phone_number': '+91 9812345678',
                'address': 'Flat 402, Green Glen Layout, Bellandur, Bengaluru',
                'latitude': 12.9279,
                'longitude': 77.6727
            }
        )
        patient_user.set_password('password123')
        patient_user.save()

        patient_profile, _ = PatientProfile.objects.get_or_create(
            user=patient_user,
            defaults={
                'blood_group': 'O+',
                'dob': date(1992, 5, 14),
                'gender': 'MALE',
                'emergency_contact': '+91 9812345679',
                'medical_history': 'Mild dust allergy, no chronic conditions.'
            }
        )

        lab_user, _ = User.objects.get_or_create(
            username='lab_demo',
            defaults={
                'email': 'contact@apollodiagnostics.com',
                'role': User.Role.DIAGNOSTICIAN,
                'phone_number': '+91 8023456789',
                'address': '100 Feet Road, Indiranagar, Bengaluru',
                'latitude': 12.9784,
                'longitude': 77.6408
            }
        )
        lab_user.set_password('password123')
        lab_user.save()

        lab_profile, _ = DiagnosticianProfile.objects.get_or_create(
            user=lab_user,
            defaults={
                'lab_name': 'Apollo Diagnostics & Home Lab',
                'owner_name': 'Dr. K. S. Murthy',
                'license_number': 'KA-MED-LAB-2024-889',
                'gst_number': '29ABCDE1234F1Z5',
                'nabl_accredited': True,
                'working_hours': '07:00 AM - 09:00 PM',
                'address': lab_user.address,
                'latitude': lab_user.latitude,
                'longitude': lab_user.longitude,
                'is_home_collection_available': True,
                'is_approved_by_admin': True
            }
        )

        hospital_user, _ = User.objects.get_or_create(
            username='hospital_demo',
            defaults={
                'email': 'opd@citycarehospital.com',
                'role': User.Role.HOSPITAL,
                'phone_number': '+91 8045678901',
                'address': 'Koramangala 4th Block, Bengaluru',
                'latitude': 12.9352,
                'longitude': 77.6245
            }
        )
        hospital_user.set_password('password123')
        hospital_user.save()

        hospital_profile, _ = HospitalProfile.objects.get_or_create(
            user=hospital_user,
            defaults={
                'hospital_name': 'CityCare Multispecialty Hospital',
                'license_number': 'KA-HOSP-LIC-9921',
                'gst_number': '29AAACC9988H1Z2',
                'emergency_contact': '+91 1800-444-999',
                'working_hours': '24/7 Casualty & OPD 08:30 AM - 08:00 PM',
                'address': hospital_user.address,
                'latitude': hospital_user.latitude,
                'longitude': hospital_user.longitude,
                'is_approved_by_admin': True
            }
        )
        self.stdout.write("[OK] Demo accounts initialized (patient_demo, lab_demo, hospital_demo, admin_demo / password123)")

        # 3. Symptoms
        symptoms_data = [
            ('Fever', 'Elevated body temperature above 98.6F'),
            ('Cold & Cough', 'Nasal congestion, sore throat, sneezing'),
            ('Weakness & Fatigue', 'General body lethargy, tiredness'),
            ('Vomiting & Nausea', 'Abdominal discomfort and emesis'),
            ('Chest Pain', 'Tightness or discomfort in chest area'),
            ('Diabetes / High Sugar', 'Frequent urination, excessive thirst'),
            ('Thyroid Problem', 'Weight changes, fatigue, hair thinning'),
            ('Skin Rash & Allergy', 'Itching, redness, or cutaneous eruptions'),
            ('Joint & Bone Pain', 'Arthralgia or musculoskeletal stiffness'),
        ]
        symptom_objs = {}
        for sname, sdesc in symptoms_data:
            s_obj, _ = Symptom.objects.get_or_create(name=sname, defaults={'description': sdesc})
            symptom_objs[sname] = s_obj

        # 4. Symptom Test Mappings
        mappings_data = [
            ('Fever', 'CBC', 5),
            ('Fever', 'Dengue RT-PCR', 4),
            ('Fever', 'Typhoid Serology', 4),
            ('Fever', 'Malaria Smear', 4),
            ('Cold & Cough', 'COVID RT-PCR', 5),
            ('Cold & Cough', 'CBC', 3),
            ('Weakness & Fatigue', 'Vitamin D', 5),
            ('Weakness & Fatigue', 'Vitamin B12', 5),
            ('Weakness & Fatigue', 'HbA1c', 4),
            ('Weakness & Fatigue', 'CBC', 4),
            ('Vomiting & Nausea', 'Liver Function Test (LFT)', 5),
            ('Vomiting & Nausea', 'Kidney Function Test (KFT)', 4),
            ('Chest Pain', 'Lipid Profile', 5),
            ('Chest Pain', 'HbA1c', 4),
            ('Diabetes / High Sugar', 'Blood Sugar Fasting & PP', 5),
            ('Diabetes / High Sugar', 'HbA1c', 5),
            ('Diabetes / High Sugar', 'Kidney Function Test (KFT)', 4),
            ('Thyroid Problem', 'Thyroid Profile (T3 T4 TSH)', 5),
        ]
        for sname, tname, weight in mappings_data:
            if sname in symptom_objs:
                SymptomTestMapping.objects.get_or_create(
                    symptom=symptom_objs[sname],
                    test_name=tname,
                    defaults={'frequency_weight': weight}
                )
        self.stdout.write("[OK] Predefined Symptoms & SymptomTestMappings populated")

        # 5. Diagnostic Tests
        tests_data = [
            ('CBC (Complete Blood Count)', 'Hematology', 350.00, 'Fasting not required', 12, True),
            ('Blood Sugar Fasting & PP', 'Diabetology', 250.00, '12 hours fasting required for Fasting sample', 8, True),
            ('HbA1c (Glycated Hemoglobin)', 'Diabetology', 550.00, 'Fasting not required', 12, True),
            ('Lipid Profile Total', 'Cardiology', 750.00, '10-12 hours overnight fasting mandatory', 24, True),
            ('Thyroid Profile (T3 T4 TSH)', 'Endocrinology', 600.00, 'Morning fasting sample preferred', 24, True),
            ('Liver Function Test (LFT)', 'Biochemistry', 800.00, 'Fasting not required', 24, True),
            ('Kidney Function Test (KFT)', 'Nephrology', 750.00, 'Fasting not required', 24, True),
            ('Vitamin D (25-OH)', 'Vitamins', 1200.00, 'Fasting not required', 36, True),
            ('Vitamin B12', 'Vitamins', 950.00, 'Fasting not required', 24, True),
            ('Dengue RT-PCR & NS1 Antigen', 'Infectious Disease', 1100.00, 'Fasting not required', 12, True),
            ('Malaria Smear & Antigen', 'Infectious Disease', 450.00, 'Fasting not required', 12, True),
            ('Typhoid Serology Widal', 'Infectious Disease', 500.00, 'Fasting not required', 12, True),
            ('COVID RT-PCR Swab', 'Virology', 700.00, 'Do not eat or drink 30 mins before swab', 12, True),
            ('Urine Routine & Microscopy', 'Urinalysis', 200.00, 'First morning mid-stream urine sample', 12, True),
            ('Urine Culture & Sensitivity', 'Microbiology', 650.00, 'Clean catch urine sample required', 48, True),
            ('Senior Citizen Health Package', 'Health Package', 1999.00, '12 hours fasting required', 24, True),
            ('Full Body Executive Checkup', 'Health Package', 2499.00, '12 hours fasting required', 24, True),
            ('Brain MRI Scan (3 Tesla)', 'Radiology', 4500.00, 'In-lab imaging procedure', 24, False),
            ('Abdomen Ultrasound Scan', 'Ultrasound', 1500.00, 'Fasting & full bladder required', 6, False),
            ('Chest X-Ray Digital', 'Radiology', 600.00, 'In-lab procedure', 2, False),
        ]
        for tname, cat, price, prep, dur, home_comp in tests_data:
            DiagnosticTest.objects.get_or_create(
                lab=lab_profile,
                name=tname,
                defaults={
                    'category': cat,
                    'price': price,
                    'preparation': prep,
                    'duration_hours': dur,
                    'is_home_collection_compatible': home_comp
                }
            )
        self.stdout.write("[OK] Diagnostic Tests catalog populated")

        # 6. Technicians
        Technician.objects.get_or_create(lab=lab_profile, name='Ramesh Kumar', defaults={'phone': '+91 9876500001', 'area': 'Indiranagar / Domlur', 'is_available': True})
        Technician.objects.get_or_create(lab=lab_profile, name='Suresh Singh', defaults={'phone': '+91 9876500002', 'area': 'Koramangala / HSR', 'is_available': True})

        # 7. Departments & Doctors for Hospital
        depts_data = [
            ('General Medicine', 'Primary care and internal medicine'),
            ('Cardiology', 'Heart, blood vessels, and cardiovascular health'),
            ('Neurology', 'Brain, spinal cord, and nerve disorders'),
            ('ENT', 'Ear, Nose, Throat, and Head-Neck care'),
            ('Orthopedics', 'Bones, joints, ligaments, and spine'),
            ('Gynecology', 'Obstetrics, pregnancy, and women health'),
            ('Pediatrics', 'Child healthcare, growth, and immunization'),
            ('Dental', 'Oral healthcare and dentistry'),
            ('Dermatology', 'Skin, hair, and cosmetic dermatology'),
        ]
        dept_objs = {}
        for dname, ddesc in depts_data:
            d_obj, _ = Department.objects.get_or_create(hospital=hospital_profile, name=dname, defaults={'description': ddesc})
            dept_objs[dname] = d_obj

        doctors_data = [
            ('Rajesh Sharma', 'General Medicine', 'MBBS, MD (Internal Medicine)', 'General Physician', 12, 600.00),
            ('Ananya Verma', 'Cardiology', 'MBBS, MD, DM (Cardiology)', 'Cardiologist', 15, 1000.00),
            ('Priya Nambiar', 'Dermatology', 'MBBS, MD (Dermatology)', 'Dermatologist', 9, 800.00),
            ('Vikram Rao', 'ENT', 'MBBS, MS (ENT)', 'ENT Specialist', 11, 700.00),
            ('Sunita Patil', 'Pediatrics', 'MBBS, MD (Pediatrics)', 'Pediatrician', 10, 750.00),
            ('Karthik Reddy', 'Orthopedics', 'MBBS, MS (Orthopedics)', 'Orthopedic Surgeon', 14, 900.00),
        ]
        for dname, dept_name, qual, spec, exp, fee in doctors_data:
            if dept_name in dept_objs:
                Doctor.objects.get_or_create(
                    hospital=hospital_profile,
                    name=dname,
                    defaults={
                        'department': dept_objs[dept_name],
                        'qualification': qual,
                        'specialization': spec,
                        'experience_years': exp,
                        'consultation_fee': fee,
                        'available_days': 'Mon, Tue, Wed, Thu, Fri, Sat',
                        'available_time_start': '09:00:00',
                        'available_time_end': '17:00:00'
                    }
                )
        self.stdout.write("[OK] Hospital Departments & Doctors roster populated")

        # 8. Coupons & Offers
        Coupon.objects.get_or_create(
            code='HEALTH10',
            defaults={
                'discount_percent': 10.00,
                'discount_max_amount': 300.00,
                'min_order_amount': 500.00,
                'valid_until': date(2027, 12, 31),
                'is_active': True,
                'usage_limit': 500
            }
        )
        Coupon.objects.get_or_create(
            code='WELCOME20',
            defaults={
                'discount_percent': 20.00,
                'discount_max_amount': 500.00,
                'min_order_amount': 800.00,
                'valid_until': date(2027, 12, 31),
                'is_active': True,
                'usage_limit': 1000
            }
        )

        Offer.objects.get_or_create(
            title='Monsoon Health Checkup Offer',
            defaults={
                'description': 'Flat 20% OFF on Full Body Executive Checkups & Free Home Collection.',
                'discount_percentage': 20.00,
                'valid_until': date(2027, 12, 31),
                'is_active': True
            }
        )

        # 9. Reviews & Ratings
        Review.objects.get_or_create(
            user=patient_user,
            target_type='LAB',
            target_id=lab_profile.id,
            defaults={'rating': 5, 'comment': 'Excellent home sample collection. Technician arrived right on time.'}
        )
        Review.objects.get_or_create(
            user=patient_user,
            target_type='HOSPITAL',
            target_id=hospital_profile.id,
            defaults={'rating': 5, 'comment': 'Clean OPD environment and polite doctors.'}
        )

        # 10. Medicine Reminders
        MedicineReminder.objects.get_or_create(
            patient=patient_profile,
            medicine_name='Multivitamin Supplement',
            defaults={
                'morning': True,
                'afternoon': False,
                'night': True,
                'duration_days': 30,
                'start_date': date.today(),
                'notes': 'Take after food'
            }
        )

        self.stdout.write("[SUCCESS] MediHome database seeding completed successfully! All demo records ready.")
