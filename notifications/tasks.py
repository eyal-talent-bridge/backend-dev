from celery import shared_task
from django.core.mail import send_mail, get_connection
from django.conf import settings
import logging, ssl
from django.utils import timezone
from django.conf import settings
from .models import CompanyNotification
from django.utils.timezone import now
from datetime import timedelta
from django.contrib.auth import get_user_model

User = get_user_model()

notifications_logger = logging.getLogger('notifications')

@shared_task
def custom_send_email_notification(subject, message, recipient_list):
    try:
        if settings.DEBUG:
            # Custom SSL context for debugging environment
            context = ssl.create_default_context()
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
            connection = get_connection()
            connection.ssl_context = context  # Apply the custom SSL context
        else:
            connection = get_connection()  # Use the default connection in production

        # Send emails using the connection
        send_mail(
            subject,
            message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=recipient_list,
            fail_silently=False,
            connection=connection,
        )
        notifications_logger.info(f"Email sent successfully to {recipient_list}")
    except Exception as e:
        notifications_logger.error(f"Error sending email: {str(e)}")
        raise e


@shared_task
def delete_expired_notifications():
    """Deletes all notifications whose end date is before the current date."""
    now = timezone.now()
    expired_notifications = CompanyNotification.objects.filter(end_date__lt=now)
    count = expired_notifications.count()
    expired_notifications.delete()
    notifications_logger.info(f'Deleted {count} expired notifications.')



@shared_task
def check_inactive_users_and_send_reminders():
    """Checks for users who haven't logged in for 72 hours and sends a reminder email."""
    threshold = now() - timedelta(hours=72)
    inactive_users = User.objects.filter(last_login__lt=threshold)

    if inactive_users.exists():
        notifications_logger.info(f"Found {inactive_users.count()} inactive users.")
    else:
        notifications_logger.info("No inactive users found.")

    # Send reminder email to inactive users
    for user in inactive_users:
        if user.email:
            try:
                # Send each email as a Celery task for asynchronous execution
                send_reminder_email.delay(user.email)
            except Exception as e:
                notifications_logger.error(f"Error scheduling reminder for {user.email}: {str(e)}")
        else:
            notifications_logger.warning(f"User {user.username} does not have an email address.")


@shared_task(bind=True, max_retries=3)
def send_reminder_email(self, user_email):
    """Helper function to send reminder email to inactive users."""
    subject = "We miss you!"
    message = "It looks like you haven't logged in for a while. Come back and check out what's new!"
    from_email = "talent-bridge@noreply.org"

    try:
        send_mail(
            subject,
            message,
            from_email,
            [user_email],
            fail_silently=False,
        )
        notifications_logger.info(f"Reminder email sent to {user_email}")
    except Exception as e:
        notifications_logger.error(f"Error sending reminder email to {user_email}: {str(e)}")
        # Retry sending the email if there is an error
        self.retry(exc=e, countdown=60)  # Retry after 60 seconds