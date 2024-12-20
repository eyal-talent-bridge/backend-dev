import logging,requests
from .models import *
import os

NOTIFICATION_SERVICE_URL=os.getenv('NOTIFICATION_SERVICE_URL',"http://localhost:8070/api/v1/notifications/")
users_logger = logging.getLogger('users')
# -------------------------------------Talents-----------------------------------------------------------------------------------------------------------------------------------------------

def trigger_signup_notification(user_email):
    url = f"{NOTIFICATION_SERVICE_URL}send-signup-notification/"

    data = {'user_email': user_email}

    try:
        # Log the start of the request
        users_logger.info(f"Attempting to send signup notification to {user_email}")

        # Send the POST request to the notifications service
        response = requests.post(url, json=data)
        if response.status_code == 200:
            users_logger.info(f"Notification email sent successfully to {user_email}")
            return "Notification email sent successfully."
        else:
            users_logger.error(f"Failed to send notification email to {user_email}. Status code: {response.status_code}")
            return f"Failed to send notification email. Status code: {response.status_code}"

    except requests.exceptions.RequestException as e:
        # Log any request-related exceptions
        users_logger.error(f"Error occurred while sending signup notification to {user_email}: {str(e)}")
        return f"Failed to send notification email due to an error: {str(e)}"
    



def trigger_inactive_user_check(user_email):
    url = f"{NOTIFICATION_SERVICE_URL}trigger-inactive-user-check/"

    data = {'user_email': user_email}

    try:
        # Log the start of the request
        users_logger.info(f"Attempting to send inactive notification to {user_email}")

        # Send the POST request to the notifications service
        response = requests.post(url, json=data)
        if response.status_code == 200:
            users_logger.info(f"Notification email sent successfully to {user_email}")
            return "Notification email sent successfully."
        else:
            users_logger.error(f"Failed to send notification email to {user_email}. Status code: {response.status_code}")
            return f"Failed to send notification email. Status code: {response.status_code}"

    except requests.exceptions.RequestException as e:
        # Log any request-related exceptions
        users_logger.error(f"Error occurred while sending inactive notification to {user_email}: {str(e)}")
        return f"Failed to send notification email due to an error: {str(e)}"
    
