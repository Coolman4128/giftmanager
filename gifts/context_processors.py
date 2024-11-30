from .models import Notification

def notifications_context(request):
    if request.user.is_authenticated:
        has_notifications = Notification.objects.filter(user_sent_to=request.user).exists()
    else:
        has_notifications = False
    return {'has_notifications': has_notifications}