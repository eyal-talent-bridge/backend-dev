import re,logging,os
from rest_framework.response import Response
from django.core.exceptions import ValidationError
from .models import *
from urllib.parse import urlparse
from PyPDF2 import PdfReader
import requests


users_logger = logging.getLogger('users')
cv_logger = logging.getLogger('cv')
# -------------------------------------Talents-----------------------------------------------------------------------------------------------------------------------------------------------

def validate_talent_email(email):
    public_domains = ['gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com']
    domain = email.split('@')[1]
    if domain not in public_domains:
        Response({'status': 'error', 'message': 'Invalid email or password'},False)
    return True


def scan_cv_for_job_requirements(cv_file, job_requirements):
    # Log if CV is not provided
    if not cv_file:
        cv_logger.info("No CV is defined for this talent.")
        return 0

    try:
        cv_logger.info(f"Scanning CV: {cv_file.name}")
        
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
                        cv_logger.warning(f"Page {pdf_reader.pages.index(page) + 1} has no extractable text in CV: {cv_file.name}.")
        else:
            # Process text files
            with open(cv_file.path, 'r') as file:
                cv_content = file.read().lower()

        # Convert CV content and job requirements to sets for faster matching
        cv_words = set(cv_content.split())  # Split CV into words
        job_requirements_set = set([req.strip().lower() for req in job_requirements if isinstance(req, str)])
        
        # Check intersection between CV words and job requirements
        matches = len(cv_words.intersection(job_requirements_set))

        cv_logger.info(f"Total matches found: {matches} for {len(job_requirements)} job requirements in CV: {cv_file.name}.")

        return matches

    except Exception as e:
        users_logger.error(f"Error analyzing CV: {cv_file.name}. Error: {e}", exc_info=True)
        return 0




# calculate distance btween job to talent
    
# API_KEY = 'YOUR_GOOGLE_MAPS_API_KEY'

# # Function to get coordinates (latitude and longitude) of a location
# def get_coordinates(location):
#     url = f"https://maps.googleapis.com/maps/api/geocode/json?address={location}&key={API_KEY}"
#     response = requests.get(url)
#     data = response.json()
#     if data['status'] == 'OK':
#         coordinates = data['results'][0]['geometry']['location']
#         return coordinates['lat'], coordinates['lng']
#     else:
#         raise ValueError(f"Geocoding failed for location: {location}")

# # Function to get the distance between two coordinates
# def get_distance(job_place, birth_place):
#     job_lat, job_lng = get_coordinates(job_place)
#     birth_lat, birth_lng = get_coordinates(birth_place)
    
#     url = f"https://maps.googleapis.com/maps/api/distancematrix/json?units=metric&origins={job_lat},{job_lng}&destinations={birth_lat},{birth_lng}&key={API_KEY}"
    
#     response = requests.get(url)
#     data = response.json()
    
#     if data['status'] == 'OK':
#         distance = data['rows'][0]['elements'][0]['distance']['text']  # Get distance text (in km or miles)
#         duration = data['rows'][0]['elements'][0]['duration']['text']  # Get duration text
#         return distance, duration
#     else:
#         raise ValueError("Distance calculation failed")

# # Example usage
# job_place = "Berlin, Germany"
# birth_place = "Paris, France"

# distance, duration = get_distance(job_place, birth_place)
# print(f"The distance between {job_place} and {birth_place} is {distance}, and it takes approximately {duration}.")
# ----------------------------------------------------------Company--------------------------------------------------------------------------------------------------------------------

def validate_company_email(email):
    public_domains = ['gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com']
    domain = email.split('@')[1]
    if domain in public_domains:
        Response({'status': 'error', 'message': 'Invalid email or password'},False)
    return True

def validate_website_url(url):
    if not url:
        return False
    
    # Check if the URL starts with http:// or https://
    if not re.match(r'^https?://', url):
        return False
    
    # Use urlparse to further validate the URL structure
    parsed_url = urlparse(url)
    if not parsed_url.scheme or not parsed_url.netloc:
        return False
    
    return True




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

