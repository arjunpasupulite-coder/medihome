from django.urls import path
from . import views

app_name = 'patients'

urlpatterns = [
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('diagnostics/search/', views.diagnostic_search_view, name='diagnostic_search'),
    path('diagnostics/test/<str:test_name>/labs/', views.test_lab_search_view, name='test_lab_search'),
    path('diagnostics/recommendations/', views.symptom_recommendation_view, name='symptom_recommendations'),
    path('labs/search/', views.lab_search_view, name='lab_search'),
    path('cart/', views.cart_view, name='cart'),
    path('cart/add/<int:test_id>/', views.add_to_cart_view, name='add_to_cart'),
    path('cart/remove/<int:item_id>/', views.remove_from_cart_view, name='remove_from_cart'),
    path('cart/clear/', views.clear_cart_view, name='clear_cart'),
    path('checkout/', views.checkout_view, name='checkout'),
    path('bookings/', views.patient_bookings_history_view, name='booking_history'),
    path('booking/<int:booking_id>/', views.booking_detail_view, name='booking_detail'),
    path('booking/process-payment/', views.process_booking_payment_view, name='process_booking_payment'),
    path('reminders/', views.medicine_reminders_view, name='medicine_reminders'),
    path('reminders/add/', views.add_medicine_reminder_view, name='add_medicine_reminder'),
    path('reminders/delete/<int:reminder_id>/', views.delete_medicine_reminder_view, name='delete_medicine_reminder'),
]
