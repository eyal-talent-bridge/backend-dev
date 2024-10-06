
from .tasks import custom_send_email_notification
import logging
from django.conf import settings
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from backend.settings import FRONTEND_URL

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