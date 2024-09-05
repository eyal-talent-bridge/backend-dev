import re,logging
from rest_framework.response import Response
from django.core.exceptions import ValidationError
from .models import *
users_logger = logging.getLogger('users')
# -------------------------------------Talents-----------------------------------------------------------------------------------------------------------------------------------------------

def validate_talent_email(email):
    public_domains = ['gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com']
    domain = email.split('@')[1]
    if domain not in public_domains:
        Response({'status': 'error', 'message': 'Invalid email or password'},False)
    return True


# Scan CV function
def scan_cv_for_job_requirements(cv_file, job_requirements):
    if not cv_file:
        return 0

    try:
        with open(cv_file.path, 'r') as file:
            cv_content = file.read().lower()

        matches = 0
        for requirement in job_requirements:
            if re.search(re.escape(requirement), cv_content):
                matches += 1

        return matches
    except Exception as e:
        users_logger.error(f"Error analyzing CV: {e}")
        return 0
    

# ----------------------------------------------------------Company--------------------------------------------------------------------------------------------------------------------

def validate_company_email(email):
    public_domains = ['gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com']
    domain = email.split('@')[1]
    if domain in public_domains:
        Response({'status': 'error', 'message': 'Invalid email or password'},False)
    return True

def validate_company_website(website):
    if not website:
        return False
    if not re.match(r'^https?://', website):
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





def validate_password_strength(password, email=None, first_name=None, last_name=None):
    # Minimum length
    if len(password) < 8:
        raise ValidationError("Password must be at least 8 characters long.")

    # Check for complexity: must contain at least one uppercase letter, one lowercase letter, one digit, and one special character
    if not re.search(r'[A-Z]', password):
        raise ValidationError("Password must contain at least one uppercase letter (A-Z).")
    if not re.search(r'[a-z]', password):
        raise ValidationError("Password must contain at least one lowercase letter (a-z).")
    if not re.search(r'\d', password):
        raise ValidationError("Password must contain at least one digit (0-9).")
    if not re.search(r'[!@#$%^&*()_\-+=\[\]{};:,.<>?/]', password):
        raise ValidationError("Password must contain at least one special character (!@#$%^&*() etc.).")

    # Avoid passwords that contain parts of the user's personal information
    if email and email.split('@')[0].lower() in password.lower():
        raise ValidationError("Password should not contain parts of your email address.")
    if first_name and first_name.lower() in password.lower():
        raise ValidationError("Password should not contain your first name.")
    if last_name and last_name.lower() in password.lower():
        raise ValidationError("Password should not contain your last name.")

    # Avoid common passwords or sequential characters
    common_passwords = ['password', '123456', '123456789', 'qwerty', 'abc123', 'password123']
    if password.lower() in common_passwords:
        raise ValidationError("Password is too common.")
    if re.search(r'(.)\1{2,}', password) or re.search(r'12345', password):
        raise ValidationError("Password must not contain sequences or repeated characters.")

    return True
