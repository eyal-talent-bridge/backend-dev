
import datetime 
from .tasks import custom_send_email_notification
import logging
from django.conf import settings
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from backend.settings import FRONTEND_URL
from rest_framework import status
from .models import CompanyNotification
from .serializers import CompanyNotificationSerializer
from users.models import Recruiter,Company


notifications_logger = logging.getLogger('notifications')


def signup_notification(request,user_email):
    subject = 'Welcome to Talent-Bridge'
    message = (
    "Hi,\n\n"
    "Thank you for signing up with Talent-Bridge! 🎉 We're thrilled to have you on board.\n\n"
    "At Talent-Bridge, we strive to connect talents and opportunities seamlessly. Whether you're looking "
    "to expand your professional network or find your next career move, you're in the right place!\n\n"
    "Here's what you can do next:\n"
    "- Complete your profile to increase your visibility.\n"
    "- Explore available job opportunities and start connecting.\n"
    "- Stay tuned for personalized job recommendations and updates.\n\n"
    "If you have any questions, feel free to reach out to our support team at support@talent-bridge.org.\n\n"
    "Once again, welcome aboard! 🚀\n\n"
    "Best regards,\n"
    f"The Talent-Bridge Team\n {FRONTEND_URL}"
)
    recipient_list = [user_email]

    # Call the Celery task
    custom_send_email_notification(subject, message, recipient_list)
    notifications_logger.info(f"Notification has been sent to {user_email}")
    return Response({"message":"Notification email sent."})





@api_view(['POST'])
@permission_classes([IsAuthenticated])
def contact_us(request):
    first_name = request.data.get('firstName')
    last_name = request.data.get('lastName'," ") 
    email = request.data.get('email')
    subject = request.data.get('subject')
    message = request.data.get('message')

    email_subject = {subject}
    email_message = f"From: {first_name} {last_name}\nEmail: {email}\n\nMessage:\n{message}"
    custom_send_email_notification(subject=email_subject, message=email_message, recipient_list=[settings.SUPPORT_EMAIL])
    notifications_logger.info(f"Contact us notification has been sent to {settings.DEFAULT_FROM_EMAIL}")
    return Response({"message": "Notification email sent."})





# newsletter 
@api_view(['POST'])
def send_newsletter(request):
    """
    Endpoint to send a newsletter to a list of users.
    Expects `message` and `users_list` in the request data.
    """
    try:
        # Extract message and users_list from request data
        message = request.data.get('message', None)
        users_list = request.data.get('users_list', None)
        
        # Validate input
        if not message or not users_list:
            return Response({"error": "Both 'message' and 'users_list' are required."}, status=400)

        subject = 'Newsletter from Talent-Bridge'
        
        # Loop through the users_list and send the email
        for user_email in users_list:
            # Format the email message
            formatted_message = (
                f"Hi,\n\n"
                f"{message}\n\n"
                f"Best regards,\n"
                f"The Talent-Bridge Team\n{FRONTEND_URL}"
            )
            recipient_list = [user_email]
            
            # Call the Celery task (you can call `send_mail` directly if not using Celery)
            custom_send_email_notification.delay(subject, formatted_message, recipient_list)
            
            # Log the sent notification
            notifications_logger.info(f"Newsletter has been sent to {user_email}")
        
        return Response({"message": "Newsletter sent successfully."}, status=200)
    
    except Exception as e:
        notifications_logger.error(f"Failed to send newsletter: {str(e)}")
        return Response({"error": "An error occurred while sending the newsletter."}, status=500)
    



@api_view(['POST', 'GET'])
@permission_classes([IsAuthenticated])
def manage_company_notifications(request, company_id):
    if request.method == 'POST':
        notifications_logger.info(f"Creating notifications for company_id {company_id}")

        recipients = request.data.get('recipients')  # Recipients can be "all_recruiters" or a list of divisions
        subject = request.data.get('subject')
        message = request.data.get('message')
        end_date = request.data.get('end_date', datetime.datetime.now() + datetime.timedelta(days=7))

        if not subject or not message:
            notifications_logger.error("Subject or message missing in the request")
            return Response({'error': 'Subject and message are required'}, status=status.HTTP_400_BAD_REQUEST)

        notifications = []

        try:
            company = Company.objects.filter(user_id=company_id).first()
            if not company:
                notifications_logger.error(f"Company not found for user_id {company_id}")
                return Response({'error': 'Company not found'}, status=status.HTTP_404_NOT_FOUND)

            if recipients == "all_recruiters":
                notifications_logger.info(f"Sending notifications to all recruiters of company {company_id}")
                recruiters = Recruiter.objects.filter(company=company)
            else:
                if not isinstance(recipients, list):
                    return Response({'error': 'Recipients must be a list of divisions or "all_recruiters"'}, status=status.HTTP_400_BAD_REQUEST)

                divisions = recipients
                notifications_logger.info(f"Sending notifications to divisions {divisions} of company {company_id}")
                recruiters = Recruiter.objects.filter(company=company, division__in=divisions)

                if not recruiters.exists():
                    notifications_logger.warning(f"No recruiters found for divisions {divisions} in company {company_id}")
                    return Response({'error': f'No recruiters found for divisions {divisions}'}, status=status.HTTP_404_NOT_FOUND)

            for recruiter in recruiters:
                try:
                    notification = CompanyNotification.objects.create(
                        recipient=recruiter,  # Use the recruiter instance here, not recruiter.user
                        subject=subject,
                        message=message,
                        end_date=end_date
                    )
                    notifications.append(notification)
                except Exception as e:
                    notifications_logger.error(f"Failed to create notification for recruiter {recruiter.id}: {str(e)}")

            serializer = CompanyNotificationSerializer(notifications, many=True)
            notifications_logger.info(f"Successfully created {len(notifications)} notifications")
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        except Exception as e:
            notifications_logger.error(f"Error creating notifications: {str(e)}")
            return Response({'error': 'An error occurred while creating notifications'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    elif request.method == 'GET':
        notifications_logger.info(f"Fetching notifications for company_id {company_id}")

        try:
            # Fetch the company based on the company_id
            company = Company.objects.get(user_id=company_id)
            # Get recruiters for this company
            recruiters = Recruiter.objects.filter(company=company)
            # Fetch notifications for these recruiters
            notifications = CompanyNotification.objects.filter(recipient__in=recruiters)
            
            serializer = CompanyNotificationSerializer(notifications, many=True)
            notifications_logger.info(f"Fetched {len(notifications)} notifications for company {company_id}")
            return Response(serializer.data, status=status.HTTP_200_OK)

        except Exception as e:
            notifications_logger.error(f"Error fetching notifications for company {company_id}: {str(e)}")
            return Response({'error': 'An error occurred while fetching notifications'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)