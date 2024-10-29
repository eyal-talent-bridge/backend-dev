import re,logging,os,requests
from rest_framework.response import Response
from .models import *
from urllib.parse import urlparse
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


# ---------------------------------Recruiter---------------------------------------------------------------------------------------
def validate_recruiter_email(email, company_id):
    # Fetch the company associated with the given company_id
    company = Company.objects.filter(id=company_id).first()
    
    # If company doesn't exist, return an error
    if not company:
        return Response({'status': 'error', 'message': 'Company not found'}, status=400)

    # Extract domain from company's email and recruiter's email
    company_domain = company.email.split('@')[1] if company.email else None
    recruiter_domain = email.split('@')[1]
    
    # Check if company has a valid domain and if the domains match
    if not company_domain or company_domain != recruiter_domain:
        return Response({'status': 'error', 'message': 'Email domain does not match company domain'}, status=400)

    # Return True if validation is successful
    return True
        

    
    



# def validate_working_days(self, value):
#         valid_days = {'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'}
#         if not set(value).issubset(valid_days):
#             raise serializers.ValidationError("Working days must be a subset of valid weekdays.")
#         return value

# def validate_working_hours(self, value):
#         if not isinstance(value, dict):
#             raise serializers.ValidationError("Expected a dictionary for working hours.")

#         for day, hours in value.items():
#             if not isinstance(hours, dict) or 'start' not in hours or 'end' not in hours:
#                 raise serializers.ValidationError(f"Invalid working hours format for {day}. Expected a dict with 'start' and 'end' times.")
            
#             start_time = hours['start']
#             end_time = hours['end']
            
#             if not (isinstance(start_time, str) and isinstance(end_time, str)):
#                 raise serializers.ValidationError(f"Working hours for {day} should be in string format.")
            
#             try:
#                 start_hour, start_minute = map(int, start_time.split(':'))
#                 end_hour, end_minute = map(int, end_time.split(':'))
#             except ValueError:
#                 raise serializers.ValidationError(f"Invalid time format for {day}. Expected 'HH:MM' format.")
            
#             if not (0 <= start_hour < 24 and 0 <= end_hour < 24):
#                 raise serializers.ValidationError(f"Hour value out of range for {day}.")
#             if not (0 <= start_minute < 60 and 0 <= end_minute < 60):
#                 raise serializers.ValidationError(f"Minute value out of range for {day}.")
#             if (start_hour, start_minute) >= (end_hour, end_minute):
#                 raise serializers.ValidationError(f"End time must be after start time for {day}.")
        
#         return value


def validate_phone_number(phone_number):
    if not phone_number.isdigit() or len(phone_number) < 9 or len(phone_number) > 15 :
         Response({'status': 'error', 'message':"Enter a valid phone number."},False)
    return True



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