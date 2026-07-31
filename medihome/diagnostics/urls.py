from django.urls import path
from . import views

app_name = 'diagnostics'

urlpatterns = [
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('bookings/', views.booking_list_view, name='booking_list'),
    path('booking/<int:booking_id>/update-status/', views.update_booking_status_view, name='update_booking_status'),
    path('tests/', views.test_list_view, name='test_list'),
    path('tests/add/', views.test_add_view, name='test_add'),
    path('tests/edit/<int:test_id>/', views.test_edit_view, name='test_edit'),
    path('tests/delete/<int:test_id>/', views.test_delete_view, name='test_delete'),
    path('technicians/', views.technician_list_view, name='technician_list'),
    path('technicians/add/', views.technician_add_view, name='technician_add'),
    path('technicians/edit/<int:tech_id>/', views.technician_edit_view, name='technician_edit'),
    path('technicians/delete/<int:tech_id>/', views.technician_delete_view, name='technician_delete'),
    path('revenue/', views.revenue_analytics_view, name='revenue'),
]
