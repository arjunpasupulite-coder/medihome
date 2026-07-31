from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Notification

@login_required
def feed_view(request):
    notifications = Notification.objects.filter(user=request.user)
    
    # Mark as read
    if request.method == 'POST':
        notifications.update(is_read=True)
        return redirect('notifications:feed')

    return render(request, 'notifications/feed.html', {
        'notifications': notifications
    })
