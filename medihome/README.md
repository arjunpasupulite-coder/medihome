# MediHome – Smart Home Diagnostic & Digital Health Record System

> **Tagline**: Book Diagnostic Tests, Hospital Appointments, and Access Health Records – All in One Platform.

MediHome is a full-stack, production-quality Django web application built using Python, Django ORM, MySQL, HTML5, CSS3, and Vanilla JavaScript. It serves as a unified digital healthcare ecosystem for Patients, Diagnostician Laboratories, Hospitals, and System Administrators.

---

## 🌟 Key Features

### 1. Multi-Role Authentication & Access Control
- **3 Independent Roles**: Patient, Diagnostician, and Hospital with custom registration and login portals.
- **Admin Approval Requirement**: Diagnostician laboratories and hospitals require explicit Administrator approval before accepting live orders or appointments.
- **Role-Based Decorators**: `@patient_required`, `@diagnostician_required`, `@hospital_required`, and `@admin_required`.
- **Activity Audit Trail**: Real-time `ActivityLog` entries tracking IP addresses and user actions across registrations, logins, profile edits, and logouts.

### 2. Patient Diagnostic Module
- **Option 1 (Direct Test Search)**: Filterable catalog displaying home sample collection tests. Enforces domain rules by strictly excluding imaging/in-lab procedures (MRI, CT Scan, PET Scan, Ultrasound, X-Ray, Endoscopy, Colonoscopy, EEG).
- **Option 2 (Symptom Recommendation Engine)**: Pure database frequency matching (`SymptomTestMapping`) with star ratings (★★★★★ CBC, ★★★★ Dengue, etc.) and a mandatory medical disclaimer.
- **Laboratory Search**: Search partner labs by query, dynamic rating (aggregated from `Review` model), distance (Haversine formula), home collection availability, and active promotional offers.
- **Cart & Checkout Engine**: Backend recalculates all figures (`subtotal`, `gst_amount`, `platform_fee`, `home_collection_fee`, `discount_amount`, `grand_total`). Never trusts frontend values.
- **Dynamic SystemSettings**: GST %, Platform Fee, and Home Collection Charge are fetched dynamically from the `SystemSettings` database model.

### 3. Booking Lifecycle Tracking & Reports
- **8-Stage Live Tracker Bar**:
  `Booking Confirmed` → `Technician Assigned` → `Technician On The Way` → `Sample Collected` → `Reached Laboratory` → `Testing` → `Report Uploaded` → `Completed`.
- **Audit Timeline**: Every status update generates a `BookingStatusHistory` record with `timestamp`, `status`, `updated_by`, and `notes`.
- **Electronic Medical Reports**: Secure PDF report view and download with strict file validation (PDF extension only, max 5MB). Physical hard copy delivery request toggle.
- **Medicine Reminders**: Daily dosage schedule (Morning 🌅, Afternoon ☀️, Night 🌙) with automated course expiration tracking.
- **Telemedicine Suite**: Encrypted video call placeholder room UI, live chat thread history (`ChatMessage`), doctor consultation notes, and prescription PDF upload.

### 4. Hospital OPD & Doctor Management
- **OP Consultation Booking**: Hospital → Department → Doctor → Dynamic 30-Minute Time Slots → Payment → Confirmation.
- **Double Booking Protection**: Prevents duplicate bookings for the same doctor, date, and time slot by automatically hiding booked slots.
- **Doctor Recommendation Engine**: Predefined symptom-to-specialty mapping (Fever → General Physician, Chest Pain → Cardiologist, Skin Rash → Dermatologist, etc.).
- **Hospital Dashboard**: Department CRUD, Doctor CRUD, OPD appointment management, and patient review management.

### 5. Central Admin Console & Revenue Analytics
- **Central Admin Panel**: Manage Users, Lab Approvals, Hospital Approvals, Doctors, Departments, Diagnostic Tests, Symptom Mappings, Bookings, Payments, Invoices, Coupons, Offers, Reviews, Notifications, and System Settings.
- **Revenue Analytics**: Daily, Weekly, Monthly, and Total Revenue breakdown along with top-booked tests and popular doctors.

---

## 🛠️ Technology Stack

- **Backend**: Python 3.14+, Django 6.0+ (MVT Architecture)
- **Database**: MySQL Engine (`django.db.backends.mysql`) with automatic SQLite fallback for dev execution.
- **Frontend**: HTML5, Vanilla CSS3 (Glassmorphism, CSS Grid & Flexbox, micro-animations), Vanilla JavaScript.
- **Dependencies Excluded**: NO Bootstrap, NO AJAX libraries, NO jQuery, NO React, NO Vue, NO Tailwind.

---

## 🔑 Demo User Accounts

All demo accounts are pre-configured with password: `password123`

| Role | Username | Password | Access Portal |
| :--- | :--- | :--- | :--- |
| **Patient** | `patient_demo` | `password123` | `/accounts/login/patient/` |
| **Diagnostician Lab** | `lab_demo` | `password123` | `/accounts/login/diagnostician/` |
| **Hospital** | `hospital_demo` | `password123` | `/accounts/login/hospital/` |
| **Administrator** | `admin_demo` | `password123` | `/admin/` or `/adminpanel/dashboard/` |

---

## 🚀 Installation & Setup Guide

### 1. Clone / Navigate to Project Directory
```bash
cd C:\Users\barat\.gemini\antigravity\scratch\medihome
```

### 2. Configure Environment Variables (Optional for MySQL)
By default, `medihome_proj/settings.py` is configured for MySQL. If a local MySQL server is not running, it automatically falls back to SQLite for instant out-of-the-box execution.

To connect to your custom MySQL instance, set environment variables:
```bash
export DB_ENGINE=mysql
export DB_NAME=medihome_db
export DB_USER=root
export DB_PASSWORD=your_mysql_password
export DB_HOST=localhost
export DB_PORT=3306
```

### 3. Run Database Migrations
```bash
python manage.py makemigrations
python manage.py migrate
```

### 4. Seed Initial Data & Demo Accounts
```bash
python manage.py seed_data
```

### 5. Start Development Server
```bash
python manage.py runserver 8000
```
Open your browser at `http://127.0.0.1:8000/` to access the MediHome Landing Page.

---

## 📁 Project Folder Structure

```
medihome/
├── manage.py
├── medihome_proj/
│   ├── settings.py           # MySQL config, custom User model, static/media
│   ├── urls.py               # Master URL router
│   ├── wsgi.py
│   └── asgi.py
├── static/
│   ├── css/
│   │   ├── style.css         # Healthcare design system & Glassmorphism
│   │   ├── dashboard.css     # Sidebar & statistics layout
│   │   └── components.css    # Badges, status tracker, forms, tables
│   └── js/
│       └── main.js           # Client validation & alert dismissal
├── templates/
│   ├── base.html             # Master template with top navbar & footer
│   ├── dashboard_base.html   # Role-based sidebar dashboard layout
│   ├── landing.html          # Welcome page ("Continue As")
│   ├── accounts/             # Login, Registration, Profile, Password templates
│   ├── patients/             # Diagnostic search, recommendations, cart, checkout
│   ├── diagnostics/          # Lab dashboard, test/technician CRUD, revenue
│   ├── hospitals/            # OPD booking flow, doctor/dept CRUD, recommendations
│   ├── reports/              # Report list, upload, secure PDF download
│   ├── telemedicine/         # Consultation room, live chat, prescription upload
│   └── adminpanel/           # Admin console, user management, system settings
├── accounts/                 # User role model & authentication views/forms
├── patients/                 # Patient profiles, reminders, wishlist
├── diagnostics/              # Lab profiles, tests, symptoms, cart, bookings
├── hospitals/                # Hospital profiles, depts, doctors, appointments
├── payments/                 # SystemSettings, payments, invoices, coupons
├── reports/                  # Medical reports & PDF file validators
├── notifications/            # User notifications feed
├── telemedicine/             # Consultation rooms & chat messages
└── adminpanel/               # Admin controls & review management
```

---

## 📜 License & Support

Developed for **MediHome Health Systems**. For inquiries, contact `support@medihome.com` or call `+91 1800-123-4567`.
