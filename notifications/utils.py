from django.shortcuts import get_object_or_404
from .tasks import custom_send_email_notification
from rest_framework import status
import logging
from rest_framework.response import Response
from backend.settings import FRONTEND_URL
from users.models import Job,Talent
from .models import TalentNotificationLog

notifications_logger = logging.getLogger('notifications')

def appear_on_job_search_notification(request, relevant_talents, job_id):
    job = get_object_or_404(Job, id=job_id)
    job = get_object_or_404(Job, id=job_id)

    notifications_logger.info(f"Starting notification process for job ID: {job_id}")

    if not relevant_talents:
        notifications_logger.warning(f"No relevant talents found for job ID: {job_id}")
        return Response({"message": "No relevant talents found."}, status=status.HTTP_404_NOT_FOUND)
    
    notifications_logger.info(f"Found {len(relevant_talents)} relevant talents for job ID: {job_id}")

    # Collect email addresses of relevant talents who haven't been notified yet
    users_email_list = []
    for talent in relevant_talents:
        talent_instance = Talent.objects.get(user_id=talent['user_id'])
        
        # Check if the talent has already been notified for this job
        if not TalentNotificationLog.objects.filter(talent=talent_instance, job=job).exists():
            users_email_list.append(talent['username'])
            
            # Log the notification to prevent future emails for the same job
            TalentNotificationLog.objects.create(talent=talent_instance, job=job)

    if not users_email_list:
        notifications_logger.info(f"All relevant talents have already been notified for job ID: {job_id}")
        return Response({"message": "All relevant talents have already been notified."}, status=status.HTTP_200_OK)

    notifications_logger.info(f"Email list for notification: {users_email_list}")

    subject = 'Job Opportunity Notification - Talent-Bridge'
    message = (
        "Hi,\n\n"
        "Great news! You have been identified as a potential match for a job opportunity through Talent-Bridge.\n\n"
        "Based on your skills and profile, we believe there are opportunities that could be a great fit for you. "
        "Now is the perfect time to take the next step in your career journey.\n\n"
        "Here’s what you can do:\n"
        "- Review and update your profile to ensure all your skills and experiences are highlighted.\n"
        "- Keep an eye on your dashboard for job opportunities that match your profile.\n"
        "- Actively apply to roles and engage with companies that interest you.\n\n"
        "If you have any questions or need assistance, don’t hesitate to reach out to us at support@talent-bridge.org.\n\n"
        "Wishing you the best in your career journey!\n\n"
        "Best regards,\n"
        f"The Talent-Bridge Team\n {FRONTEND_URL}"
    )
    
    # Send email to each talent in the list
    for user_email in users_email_list:
        try:
            print(user_email)
            custom_send_email_notification(subject, message, [user_email])
            notifications_logger.info(f"Notification successfully sent to {user_email}")
        except Exception as e:
            notifications_logger.error(f"Failed to send email to {user_email}. Error: {str(e)}")
    
    notifications_logger.info(f"All notification emails for job ID {job_id} have been processed.")
    return Response({"message": "Notification emails sent."}, status=status.HTTP_200_OK)