import logging,os,requests
from .models import *
from PyPDF2 import PdfReader
from backend.settings import NOTIFICATION_SERVICE_URL

users_logger = logging.getLogger('users')
# -------------------------------------Talents-----------------------------------------------------------------------------------------------------------------------------------------------

def scan_cv_for_job_requirements(cv_file, job_requirements):
    # Log if CV is not provided
    if not cv_file:
        users_logger.info("No CV is defined for this talent.")
        return 0

    try:
        users_logger.info(f"Scanning CV: {cv_file.name}")
        
        ext = os.path.splitext(cv_file.name)[1].lower()
        cv_content = ''

        if ext == '.pdf':
            # Process PDF files
            with open(cv_file.path, 'rb') as file:
                pdf_reader = PdfReader(file)
                for page in pdf_reader.pages:
                    text = page.extract_text()
                    if text:
                        cv_content += text.lower()
                    else:
                        users_logger.warning(f"Page {pdf_reader.pages.index(page) + 1} has no extractable text in CV: {cv_file.name}.")
        else:
            # Process text files
            with open(cv_file.path, 'r') as file:
                cv_content = file.read().lower()

        # Convert CV content and job requirements to sets for faster matching
        cv_words = set(cv_content.split())  # Split CV into words
        job_requirements_set = set([req.strip().lower() for req in job_requirements if isinstance(req, str)])
        
        # Check intersection between CV words and job requirements
        matches = len(cv_words.intersection(job_requirements_set))

        users_logger.info(f"Total matches found: {matches} for {len(job_requirements)} job requirements in CV: {cv_file.name}.")

        return matches

    except Exception as e:
        users_logger.error(f"Error analyzing CV: {cv_file.name}. Error: {e}", exc_info=True)
        return 0




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
    

def trigger_appear_on_job_search_notification(relevant_talents, job_id):
    url = f"{NOTIFICATION_SERVICE_URL}trigger-appear-on-job-search-notification/"

    data = {'relevant_talents': relevant_talents, 'job_id': str(job_id)}  # Include job_id as well

    try:
        # Log the start of the request
        users_logger.info(f"Attempting to send notification for job ID {job_id} to relevant talents")

        # Send the POST request to the notifications service
        response = requests.post(url, json=data)

        if response.status_code == 200:
            users_logger.info(f"Notification emails sent successfully for job ID {job_id}")
            return "Notification emails sent successfully."
        else:
            users_logger.error(f"Failed to send notification emails for job ID {job_id}. Status code: {response.status_code}")
            return f"Failed to send notification emails. Status code: {response.status_code}"

    except requests.exceptions.RequestException as e:
        # Log any request-related exceptions
        users_logger.error(f"Error occurred while sending notifications for job ID {job_id}: {str(e)}")
        return f"Failed to send notification emails due to an error: {str(e)}"