from django.urls import path
from . import views

app_name = 'hospitals'

urlpatterns = [
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('op-booking/', views.op_booking_hospitals_view, name='op_booking'),
    path('op-booking/hospital/<int:hospital_id>/', views.op_booking_departments_view, name='op_booking_departments'),
    path('op-booking/department/<int:department_id>/', views.op_booking_doctors_view, name='op_booking_doctors'),
    path('op-booking/doctor/<int:doctor_id>/slots/', views.op_booking_slots_view, name='op_booking_slots'),
    path('op-booking/confirm/<int:doctor_id>/', views.op_booking_confirm_view, name='op_booking_confirm'),
    path('doctor-recommendations/', views.doctor_recommendations_view, name='doctor_recommendations'),
    path('appointments/', views.appointment_list_view, name='appointment_list'),
    path('appointments/cancel/<int:appt_id>/', views.cancel_appointment_view, name='cancel_appointment'),
    
    # CRUD Routes
    path('departments/', views.department_list_view, name='department_list'),
    path('departments/add/', views.department_add_view, name='department_add'),
    path('departments/edit/<int:dept_id>/', views.department_edit_view, name='department_edit'),
    path('departments/delete/<int:dept_id>/', views.department_delete_view, name='department_delete'),
    path('doctors/', views.doctor_list_view, name='doctor_list'),
    path('doctors/add/', views.doctor_add_view, name='doctor_add'),
    path('doctors/edit/<int:doc_id>/', views.doctor_edit_view, name='doctor_edit'),
    path('doctors/delete/<int:doc_id>/', views.doctor_delete_view, name='doctor_delete'),
    path('revenue/', views.hospital_revenue_view, name='revenue'),
]
