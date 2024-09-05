
from django.http import HttpResponse
from .tasks import send_notification_email

def notify_user(request):
    subject = 'Welcome to Talent-Bridge'
    message = 'Thank you for signing up!'
    recipient_list = ['user@example.com']

    # Call the Celery task
    send_notification_email.delay(subject, message, recipient_list)

    return HttpResponse("Notification email sent.")
