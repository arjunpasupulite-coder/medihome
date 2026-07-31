from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import Payment, Invoice

@login_required
def history_view(request):
    if request.user.is_admin_role():
        payments = Payment.objects.select_related('user').all()
    else:
        payments = Payment.objects.filter(user=request.user)

    return render(request, 'payments/history.html', {
        'payments': payments
    })
