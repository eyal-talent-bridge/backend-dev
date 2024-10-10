
from celery import shared_task
from django.core.mail import send_mail, get_connection
from django.conf import settings
import logging,ssl
from django.utils import timezone
from django.conf import settings
from .models import CompanyNotification

notifications_logger = logging.getLogger('notifications')

@shared_task
def custom_send_email_notification(subject, message, recipient_list):
    try:
        if settings.DEBUG:
            context = ssl.create_default_context()
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE

            connection = get_connection()
            connection.ssl_context = context  # Apply the custom SSL context
        else:
            connection = get_connection()

        send_mail(
            subject,
            message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[settings.DEFAULT_FROM_EMAIL],
            fail_silently=False,
            connection=connection,
        )
        send_mail(subject, message, settings.EMAIL_HOST_USER, recipient_list,fail_silently=False,
            connection=connection,)
    except Exception as e:
        notifications_logger.error(f"Error sending email: {str(e)}")
        raise e


@shared_task
def delete_expired_notifications():
    now = timezone.now()
    expired_notifications = CompanyNotification.objects.filter(end_date__lt=now)
    count = expired_notifications.count()
    expired_notifications.delete()
    notifications_logger.info(f'Deleted {count} expired notifications.')
