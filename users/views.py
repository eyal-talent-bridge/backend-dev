import logging,datetime,os,time
from urllib.parse import urlencode
from urllib.request import Request
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated,AllowAny
from .serializers import *
from .models import *
from .utils import *
from django.shortcuts import get_object_or_404, redirect
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import login as auth_login, logout as logout_method
from rest_framework_simplejwt.views import TokenObtainPairView
from django.core.mail import send_mail,BadHeaderError
from django.conf import settings
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth.hashers import check_password
from django.db import IntegrityError
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from django.http import JsonResponse, HttpResponseRedirect
from django.conf import settings
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.core.exceptions import ObjectDoesNotExist





users_logger = logging.getLogger('users')
DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL')
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")
USERS_SERVICE_URL= os.getenv('USERS_SERVICE_URL','http://localhost:8000/api/v1/users/')
class MyTokenObtainPairView(TokenObtainPairView):
    serializer_class = MyTokenObtainPairSerializer

    
@api_view(['POST'])
def signin(request):
    try:
        # Get email and password from request data
        data = request.data
        username = data.get('email', '').lower().strip()
        password = data.get('password', '').strip()

        users_logger.debug(f'Attempt login for user: {username}')

        # Get the user from the database
        try:
            user = CustomUser.objects.get(username=username)
        except CustomUser.DoesNotExist:
            users_logger.info(f'Invalid login attempt for email: {username}')
            return Response({'status': 'error', 'message': 'Invalid email or password'}, status=status.HTTP_401_UNAUTHORIZED)

        # Check if the provided password is correct
        if check_password(password, user.password):
            users_logger.info(f'User authenticated: {user.username}')
            
            # Get user details
            user_type = user.user_type
            first_name = user.first_name
            last_name = user.last_name if user_type != 'Company' else ''

            # Log in the user (start the session)
            auth_login(request, user)

            # Create refresh token and add custom claims
            refresh = RefreshToken.for_user(user)
            refresh['user_type'] = user_type
            refresh['first_name'] = first_name
            refresh['last_name'] = last_name
            refresh['user_id'] = str(user.id)

            # Check if the user is a Recruiter and belongs to a company
            if user_type == 'Recruiter':
                recruiter = Recruiter.objects.filter(user=user).first()
                if recruiter and recruiter.company:
                    refresh['company_id'] = str(recruiter.company.user_id)
                else:
                    refresh['company_id'] = None

            # Generate access token as a string (no need to set it manually)
            access_token = str(refresh.access_token)

            users_logger.debug(f'{username} logged in as {user_type}')

            # Return the JWT tokens
            return Response({
                'refresh': str(refresh),
                'access': access_token
            }, status=status.HTTP_200_OK)

        else:
            # If authentication fails
            users_logger.info(f'Invalid login attempt for email: {username}')
            return Response({'status': 'error', 'message': 'Invalid email or password'}, status=status.HTTP_401_UNAUTHORIZED)

    except Exception as e:
        # Log any other error and return 500 response
        users_logger.error(f'Error logging in: {str(e)}')
        return Response({'status': 'error', 'message': 'An error occurred during login'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ----------------------------------------------Signup---------------------------------------------------

def user_signup(request,user_type):
    # Get common data from request
    email = request.data.get('email')
    password = request.data.get('password')

    # Validate user_type
    if user_type not in ['Talent', 'Company', 'Recruiter']:
        return Response({'error': 'Invalid user type'}, status=status.HTTP_400_BAD_REQUEST)

    # Check if the user with the email already exists
    if CustomUser.objects.filter(email=email).exists():
        return Response({'error': 'User with this email already exists.'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        if user_type == 'Company':
            # For Company, get name, website, and address
            name = str(request.data.get('name')).capitalize()
            website = request.data.get('website')
            address = str(request.data.get('address')).capitalize()
            phone_number = request.data.get('phone_number')

            if not validate_phone_number(phone_number):
                return Response({'error': 'Invalid company phone number'}, status=status.HTTP_400_BAD_REQUEST)



            # Create the CustomUser instance 
            user = CustomUser.objects.create_user(
                username=email,  # Use email as the username
                email=email,
                password=password,  # Hash the password
                user_type=user_type,
                first_name = name,
                last_name="",
                phone_number = phone_number
            )

            # Create the Company profile linked to the CustomUser
            Company.objects.create(
                user=user,
                name=name,
                website=website,
                address=address,   
            )
            

        elif user_type == 'Recruiter':
            # For Recruiter, get first_name, last_name, division, and position
            first_name = str(request.data.get('first_name')).capitalize()
            last_name = str(request.data.get('last_name')).capitalize()
            division = str(request.data.get('division')).capitalize()
            position = str(request.data.get('position')).capitalize()

            try:
                company_id = (request.data.get('company'))
                users_logger.info(f"Company ID (UUID): {company_id}")  # Debugging line to users_logger.info the company_id
            except ValueError:
                return Response({'message': 'Invalid company ID'}, status=status.HTTP_400_BAD_REQUEST)

            gender = request.data.get('gender')
            phone_number = request.data.get('phone_number')

            # Validate recruiter's email against the company's email domain
            # Validate phone number format
            if not validate_phone_number(phone_number):
                return Response({'message': 'Invalid recruiter phone number'}, status=status.HTTP_400_BAD_REQUEST)

            # Fetch the company using the company ID
            try:
                company = Company.objects.filter(user_id=company_id).first()
                users_logger.info(f"Company Found")  # Debugging line to confirm the company is fetched

            except Company.DoesNotExist:
                users_logger.info(f"Company with ID {company_id} not found")  # Debugging line if company not found
                return Response({'message': 'Company not found'}, status=status.HTTP_404_NOT_FOUND)

            # Create the CustomUser instance with first and last name
            user = CustomUser.objects.create_user(
                username=email,  # Use email as the username
                email=email,
                password=password,  # Hash the password
                first_name=first_name,
                last_name=last_name,
                user_type=user_type,
                phone_number=phone_number,
            )

            # Create the Recruiter profile linked to the CustomUser
            Recruiter.objects.create(
                user=user,
                company=company,  # Assign the Company object here
                division=division,
                position=position,
                gender=gender,
            )

            return Response({'message': 'Recruiter created successfully'}, status=status.HTTP_201_CREATED)
        
        else:  # Talent case
            # For Talent, get first_name and last_name
            first_name = str(request.data.get('first_name')).capitalize()
            last_name = str(request.data.get('last_name')).capitalize()
            gender = request.data.get('gender')
        
            # Create the CustomUser instance with first and last name
            user = CustomUser.objects.create_user(
                username=email,  # Use email as the username
                email=email,
                password=password,  # Hash the password
                first_name=first_name,
                last_name=last_name,
                user_type=user_type
            )

            # Create the Talent profile linked to the CustomUser
            Talent.objects.create(
                user=user,
                gender=gender
            )

        # Create a refresh token and add custom claims
        refresh = RefreshToken.for_user(user)
        refresh['user_type'] = user_type
        refresh['first_name'] = first_name if user_type != 'Company' else name
        refresh['company_id'] = company if user_type == 'Recruiter' else 'name'
        refresh['last_name'] = last_name if user_type != 'Company' else ''
        refresh['user_id'] = str(user.id)

        access = refresh.access_token

        # Log the creation of the user
        users_logger.debug(f'{email} created successfully as {user_type}')
        trigger_signup_notification(email)
        
        # Return the response with JWT tokens
        return Response({
            'status': 201,
            'user_id': user.id,
            'refresh': str(refresh),
            'access': str(access)
        }, status=status.HTTP_201_CREATED)

    except Company.DoesNotExist:
        return Response({"message": "Company not found for recruiter"}, status=status.HTTP_400_BAD_REQUEST)
    
    except Exception as e:
        users_logger.error(f"Error creating user: {e}")
        return Response({"message": f"An error occurred while creating the user, {e}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)





@api_view(['POST'])
def talent_signup(request):
    return user_signup(request, 'Talent')


@api_view(['POST'])
def recruiter_signup(request):
    return user_signup(request, 'Recruiter')


@api_view(['POST'])
def company_signup(request):
    return user_signup(request, 'Company')


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout(request):
    logout_method(request)
    users_logger.debug(f"User {request.user.email} logged out.")
    return Response({"message": "User logged out successfully."}, status=status.HTTP_200_OK)




# --------------------------------------------API---------------------------------------------------------------------
@permission_classes([IsAuthenticated])
@api_view(['GET', 'PUT', 'DELETE'])
def user_detail(request, user_id):
    # Get the user from CustomUser model
    user = get_object_or_404(CustomUser, id=user_id)
    
    # Get user_type to determine which profile and serializer to use
    user_type = user.user_type

    # Determine which serializer to use based on the user_type
    try:
        if user_type == 'Talent':
            profile = Talent.objects.get(user=user)
            serializer_class = TalentSerializer
        elif user_type == 'Company':
            profile = Company.objects.get(user=user)
            serializer_class = CompanySerializer
        elif user_type == 'Recruiter':
            profile = Recruiter.objects.get(user=user)
            serializer_class = RecruiterSerializer
        else:
            users_logger.error(f"Invalid user type: {user_type}")
            return Response({'message': 'Invalid user type'}, status=status.HTTP_400_BAD_REQUEST)
    except (Talent.DoesNotExist, Company.DoesNotExist, Recruiter.DoesNotExist):
        users_logger.error(f"Profile not found for user: {user.email}")
        return Response({'message': 'Profile not found'}, status=status.HTTP_404_NOT_FOUND)

    # Handle GET request
    if request.method == 'GET':
        # Serialize CustomUser data
        user_serializer = CustomUserSerializer(user)
        
        # Serialize profile data 
        profile_serializer = serializer_class(profile)
        
        # Combine both serialized data
        combined_data = {
            **user_serializer.data,  # CustomUser data
            **profile_serializer.data  # Profile data 
        }
        
        users_logger.debug(f"User {user.email} has been found successfully.")
        
        # Return the combined data
        return Response(combined_data,status=status.HTTP_200_OK)

    # Handle PUT request for updating CustomUser and profile data
    elif request.method == 'PUT':
        # Extract CustomUser-related fields from the request data
        user_data = {
            key: value for key, value in request.data.items()
            if key in ['id','first_name', 'last_name', 'email', 'phone_number','newsletter','accept_terms','license_type']  # Add other CustomUser fields if needed
        }

        # Update profile fields using the profile serializer
        profile_serializer = serializer_class(profile, data=request.data, partial=True)  # Allow partial updates

        # Validate the profile data first
        if profile_serializer.is_valid():
            # If user data is present, update the CustomUser fields
            if user_data:
                user_serializer = CustomUserSerializer(user, data=user_data, partial=True)
                if user_serializer.is_valid():
                    user_serializer.save()  # Save the updated CustomUser
                    user_data_to_return = user_serializer.data
                else:
                    return Response(user_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            else:
                # If no user data, fallback to the current CustomUser data
                user_data_to_return = CustomUserSerializer(user).data

            # Save the updated profile data
            profile_serializer.save()
            users_logger.debug(f"User {user.email} updated successfully.")

            # Combine updated CustomUser data and profile data
            combined_data = {
                **user_data_to_return,  # CustomUser data (updated or fallback)
                **profile_serializer.data  # Profile-specific data
            }

            return Response(combined_data, status=status.HTTP_200_OK)
        
        return Response(profile_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # Handle DELETE request
    elif request.method == 'DELETE':
        user_info = {'email': user.email, 'user_type': user.user_type}
        user.delete()
        users_logger.debug(f"User {user.email} deleted successfully.")
        return Response({'message': 'User deleted successfully', 'user_info': user_info}, status=status.HTTP_204_NO_CONTENT)

@api_view(['POST', 'DELETE'])
@permission_classes([IsAuthenticated])
def manage_cv(request, talent_id):
    try:
        # Fetch the authenticated Talent object
        talent = Talent.objects.filter(user_id=talent_id).first()
        
        if not talent:
            return Response({'message': 'Talent profile not found'}, status=status.HTTP_404_NOT_FOUND)
        
        # Handle POST request for uploading CV
        if request.method == 'POST':
            if 'cv' not in request.FILES:
                return Response({'message': 'No CV file provided'}, status=status.HTTP_400_BAD_REQUEST)
            
            # Upload the new CV
            talent.cv = request.FILES['cv']
            talent.save()

            users_logger.debug(f"CV saved for talent_id={talent_id}")
            return Response({'message': 'CV uploaded successfully!'}, status=status.HTTP_200_OK)
        
        # Handle DELETE request for deleting CV
        elif request.method == 'DELETE':
            if talent.cv:
                # Delete the CV file and update the model
                talent.cv.delete()
                talent.save()
                
                users_logger.debug(f"CV deleted for talent_id={talent_id}")
                return Response({'message': 'CV deleted successfully!'}, status=status.HTTP_200_OK)
            else:
                users_logger.debug(f"No CV to delete for talent_id={talent_id}")
                return Response({'message': 'No CV to delete'}, status=status.HTTP_404_NOT_FOUND)


    except Exception as e:
        users_logger.error(f"Error managing CV for talent_id={talent_id}: {str(e)}")
        return Response({'message': 'An error occurred while managing CV', 'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)




@api_view(['POST', 'DELETE'])
@permission_classes([IsAuthenticated])
def manage_recommendation_letter(request,user_id):
    try:
        # Get the authenticated user
        user = CustomUser.objects.filter(id=user_id).first()
        print(user.first_name)
        
        # Check if the user is a Talent and has a Talent profile
        try:
            talent = Talent.objects.get(user=user)
        except Talent.DoesNotExist:
            return Response({'message': 'Talent profile not found'}, status=status.HTTP_404_NOT_FOUND)

        if request.method == 'POST':
            talent.recommendation_letter = request.FILES.get('recommendation_letter')
            talent.save()
            return Response({'message': 'Recommendation letter uploaded successfully!'}, status=status.HTTP_200_OK)
        
        elif request.method == 'DELETE':
            if talent.recommendation_letter:
                talent.recommendation_letter.delete(save=True)
                return Response({'message': 'Recommendation letter deleted successfully!'}, status=status.HTTP_200_OK)
            else:
                return Response({'message': 'No recommendation letter to delete'}, status=status.HTTP_404_NOT_FOUND)
    
    except CustomUser.DoesNotExist:
        return Response({'message': 'Talent not found'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({'message': str(e)}, status=status.HTTP_400_BAD_REQUEST)





@api_view(['POST', 'DELETE'])
@permission_classes([IsAuthenticated])
def manage_profile_pic(request, user_id):
    try:
        # Try fetching the Talent object first
        talent = Talent.objects.filter(user_id=user_id).first()

        # If no Talent is found, try fetching the Recruiter object
        if not talent:
            recruiter = Recruiter.objects.filter(user_id=user_id).first()
            if not recruiter:
                users_logger.debug(f"Profile not found for user_id={user_id}")
                return Response({'message': 'Profile not found'}, status=status.HTTP_404_NOT_FOUND)

        # Determine if the profile is for Talent or Recruiter
        profile = talent if talent else recruiter
        profile_type = "Talent" if talent else "Recruiter"

        # Handle POST request for uploading profile picture
        if request.method == 'POST':
            if 'profile_picture' not in request.FILES:
                users_logger.debug(f"No profile picture file provided for {profile_type.lower()}_id={user_id}")
                return Response({'message': 'No profile picture file provided'}, status=status.HTTP_400_BAD_REQUEST)

            # Upload the new profile picture
            profile.profile_picture = request.FILES['profile_picture']
            profile.save()

            users_logger.debug(f"Profile picture saved for {profile_type.lower()}_id={user_id}")
            return Response({'message': 'Profile picture uploaded successfully!'}, status=status.HTTP_200_OK)

        # Handle DELETE request for deleting profile picture
        elif request.method == 'DELETE':
            if profile.profile_picture:
                # Delete the profile picture file and update the model
                profile.profile_picture.delete()
                profile.save()

                users_logger.debug(f"Profile picture deleted for {profile_type.lower()}_id={user_id}")
                return Response({'message': 'Profile picture deleted successfully!'}, status=status.HTTP_200_OK)
            else:
                users_logger.debug(f"No profile picture to delete for {profile_type.lower()}_id={user_id}")
                return Response({'message': 'No profile picture to delete'}, status=status.HTTP_404_NOT_FOUND)

    except Exception as e:
        users_logger.error(f"Error managing profile picture for user_id={user_id}: {str(e)}")
        return Response({'message': 'An error occurred while managing the profile picture', 'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



@permission_classes([IsAuthenticated])
@api_view(['GET'])
def companies_details(request, user_type='Company'):
    try:
        if user_type:
            users = CustomUser.objects.filter(user_type='Company')
        else:
            users = CustomUser.objects.all()
    except CustomUser.DoesNotExist:
        return Response({'message': 'No users were found'}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        serializer = CustomUserSerializer(users, many=True)
        users_logger.debug(f"Users have been found successfully.")
        return Response(serializer.data)



@permission_classes([IsAuthenticated])
@api_view(['GET'])
def company_recruiters(request, company_id):
    print(f"Received company_id: {company_id}")
    # Fetch the company using the provided company_id
    company = Company.objects.filter(user_id=company_id).first()
    
    if not company:
        users_logger.debug(f'Company with ID {company_id} not found.')
        return Response({'message': 'Company not found'}, status=status.HTTP_404_NOT_FOUND)

    users_logger.debug("Company found successfully.")

    # Fetch recruiters associated with the company
    recruiters = Recruiter.objects.filter(company=company)

    # Serialize each recruiter and combine their CustomUser and Recruiter profiles
    combined_data = []
    for recruiter in recruiters:
        # Serialize the user (CustomUser)
        user_serializer = CustomUserSerializer(recruiter.user)

        # Serialize the profile (Recruiter)
        profile_serializer = RecruiterSerializer(recruiter)

        # Combine both serialized data
        combined_data.append({
            **user_serializer.data,  # CustomUser data
            **profile_serializer.data  # Recruiter profile data
        })

    users_logger.debug(f"{len(recruiters)} recruiters found successfully.")

    # Return the combined data for all recruiters
    return Response(combined_data, status=status.HTTP_200_OK)


# Return open processes for a talent
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def talent_open_processes(request):
    user = CustomUser.objects.get(email=request.user.email)
    try:
        talent = Talent.objects.filter(user=user).first()
    except Talent.DoesNotExist:
        return Response({'message': 'Talent profile not found'}, status=status.HTTP_404_NOT_FOUND)

    users_logger.debug("Open processes data has been sent, status 200.")
    return Response({
        'status': 200,
        'open_processes': talent.open_processes
    }, status=200)




@api_view(['GET', 'PUT', 'DELETE', 'POST'])
@permission_classes([IsAuthenticated])
def manage_jobs(request, job_id):
    users_logger.debug(f'Request method: {request.method}, Job ID: {job_id}, User: {request.user}')

    try:
        job = Job.objects.filter(id=job_id).first()
        users_logger.debug(f'Job found: {job_id}')
    except Job.DoesNotExist:
        users_logger.debug(f'Job not found: {job_id}')
        return Response({'message': 'Job not found'}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        serializer = JobSerializer(job)
        users_logger.debug(f'Job data retrieved: {serializer.data}')
        return Response(serializer.data)

    elif request.method == 'PUT':
        serializer = JobSerializer(job, data=request.data)
        if serializer.is_valid():
            serializer.save()
            users_logger.debug(f'Job updated successfully: {serializer.data}')
            return Response(serializer.data)
        users_logger.debug(f'Job update failed: {serializer.errors}')
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'DELETE':
        job.delete()
        users_logger.debug(f'Job deleted successfully: {job_id}')
        return Response({'message': 'Job deleted successfully!'}, status=status.HTTP_200_OK)




@api_view(['POST', 'DELETE'])
@permission_classes([IsAuthenticated])
def manage_tags(request, job_id):
    users_logger.debug(f'Request method: {request.method}, Job ID: {job_id}, User: {request.user}')
    
    try:
        job = Job.objects.get(id=job_id)
        users_logger.debug(f'Job found: {job_id}')
    except Job.DoesNotExist:
        users_logger.debug(f'Job not found: {job_id}')
        return Response({'message': 'Job not found'}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'POST':
        # Adding a talent to the job
        talent_id = request.data.get('talent_id')
        match_by_cv = request.data.get('match_by_cv')
        match_by_form = request.data.get('match_by_form')
        first_name = request.data.get('first_name')
        last_name = request.data.get('last_name')

        # Validate required fields
        if not all([talent_id, match_by_cv, match_by_form, first_name, last_name]):
            return Response({'message': 'All fields are required'}, status=status.HTTP_400_BAD_REQUEST)

        relevant_talents = job.relevant_talents or []

        # Check if the talent already exists in the relevant_talents list
        if any(talent['talent_id'] == talent_id for talent in relevant_talents):
            users_logger.debug(f'Talent {talent_id} already saved to job {job_id}')
            return Response({'message': 'Talent already saved to this job'}, status=status.HTTP_400_BAD_REQUEST)

        # Append new talent to relevant_talents
        relevant_talent = {
            'talent_id': talent_id,
            'match_by_cv': match_by_cv,
            'match_by_form': match_by_form,
            'first_name': first_name,
            'last_name': last_name
        }
        relevant_talents.append(relevant_talent)
        job.relevant_talents = relevant_talents
        job.save()

        users_logger.debug(f'Talent {talent_id} added to job {job_id}')
        return Response({'message': 'Talent saved successfully!'}, status=status.HTTP_200_OK)

    elif request.method == 'DELETE':
        # Deleting a talent from the job
        talent_id = request.data.get('talent_id')

        if not talent_id:
            return Response({'message': 'Talent ID is required'}, status=status.HTTP_400_BAD_REQUEST)

        relevant_talents = job.relevant_talents or []

        # Check if the talent exists
        updated_talents = [talent for talent in relevant_talents if talent['talent_id'] != talent_id]

        if len(updated_talents) == len(relevant_talents):
            users_logger.debug(f'Talent {talent_id} not found in job {job_id}')
            return Response({'message': 'Talent not found in this job'}, status=status.HTTP_404_NOT_FOUND)

        # Save updated talents list
        job.relevant_talents = updated_talents
        job.save()

        users_logger.debug(f'Talent {talent_id} removed from job {job_id}')
        return Response({'message': 'Talent removed successfully!'}, status=status.HTTP_200_OK)

    # Method not allowed
    return Response({'message': 'Method not allowed'}, status=status.HTTP_405_METHOD_NOT_ALLOWED)




@api_view(['GET'])
@permission_classes([IsAuthenticated])
def company_jobs(request, company_id):
    try:
        # Check if the company exists
        company = Company.objects.filter(user_id=company_id).first()
        users_logger.info(f'Company found: {company_id}')

        # Fetch all jobs associated with the company
        jobs = Job.objects.filter(company=company)

        if jobs.exists():
            serializer = JobSerializer(jobs, many=True)
            users_logger.info(f"{jobs.count()} jobs were found for company {company_id}")
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            users_logger.info(f"No jobs found for company {company_id}")
            return Response({"message": "No jobs found for this company"}, status=status.HTTP_204_NO_CONTENT)

    except Company.DoesNotExist:
        users_logger.warning(f'Company not found: {company_id}')
        return Response({'message': 'Company not found'}, status=status.HTTP_404_NOT_FOUND)
    
    except ValueError:
        users_logger.error(f'Invalid UUID format: {company_id}')
        return Response({'message': 'Invalid company ID format'}, status=status.HTTP_400_BAD_REQUEST)
    
    except Exception as e:
        users_logger.error(f"Unexpected error: {str(e)}")
        return Response({'message': 'An error occurred while fetching jobs'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    

# recruiter jobs
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def recruiter_jobs(request, recruiter_id):
    try:
        # Check if the company exists
        recruiter = Recruiter.objects.filter(user_id=recruiter_id).first()
        users_logger.info(f'recruiter found: {recruiter_id}')

        # Fetch all jobs associated with the recruiter
        jobs = Job.objects.filter(recruiter=recruiter)

        if jobs.exists():
            serializer = JobSerializer(jobs, many=True)
            users_logger.info(f"{jobs.count()} jobs were found for recruiter {recruiter_id}")
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            users_logger.info(f"No jobs found for recruiter {recruiter_id}")
            return Response({"message": "No jobs found for this recruiter"}, status=status.HTTP_204_NO_CONTENT)

    except Recruiter.DoesNotExist:
        users_logger.warning(f'Recruiter not found: {recruiter_id}')
        return Response({'message': 'recruiter not found'}, status=status.HTTP_404_NOT_FOUND)
    
    except ValueError:
        users_logger.error(f'Invalid UUID format: {recruiter_id}')
        return Response({'message': 'Invalid recruiter ID format'}, status=status.HTTP_400_BAD_REQUEST)
    
    except Exception as e:
        users_logger.error(f"Unexpected error: {str(e)}")
        return Response({'message': 'An error occurred while fetching jobs'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    




@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_job(request, company_id):
    users_logger.debug(f'Create job request initiated by user: {request.user}')

    try:
        company = Company.objects.filter(user_id=company_id).first()
        # Attach the company_id to the job data
        job_data = request.data.copy()
        job_data['company'] = company.id

        serializer = JobSerializer(data=job_data)
        if serializer.is_valid():
            serializer.save()
            users_logger.debug(f'Job created successfully: {serializer.data}')
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            users_logger.debug(f'Job creation failed with errors: {serializer.errors}')
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        users_logger.debug(f'Error during job creation: {str(e)}')
        return Response({'message': 'Invalid request'}, status=status.HTTP_400_BAD_REQUEST)




@api_view(['GET', 'PUT', 'DELETE'])
def manage_recruiters(request, recruiter_id):
    users_logger.debug(f'Request method: {request.method}, Recruiter ID: {recruiter_id}, User: {request.user}')

    # Find the recruiter or return 404
    recruiter = get_object_or_404(Recruiter, id=recruiter_id)

    if request.method == 'GET':
        # Serialize both user and recruiter data
        user_serializer = CustomUserSerializer(recruiter.user)
        recruiter_serializer = RecruiterSerializer(recruiter)

        # Combine serialized data
        combined_data = {**user_serializer.data, **recruiter_serializer.data}
        users_logger.debug(f'Recruiter data retrieved: {combined_data}')
        return Response(combined_data, status=status.HTTP_200_OK)

    elif request.method == 'PUT':
        # Update recruiter data
        serializer = RecruiterSerializer(recruiter, data=request.data)
        if serializer.is_valid():
            serializer.save()
            users_logger.debug(f'Recruiter updated successfully: {serializer.data}')
            return Response(serializer.data, status=status.HTTP_200_OK)
        users_logger.debug(f'Recruiter update failed: {serializer.errors}')
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'DELETE':
        # Delete recruiter
        recruiter.delete()
        users_logger.debug(f'Recruiter deleted successfully: {recruiter_id}')
        return Response({'message': 'Recruiter deleted successfully!'}, status=status.HTTP_200_OK)

    users_logger.debug(f'Invalid request method: {request.method}')
    return Response({'message': 'Invalid request method'}, status=status.HTTP_405_METHOD_NOT_ALLOWED)

#---------------------------------------------Social login--------------------------------------------------------

@api_view(['POST'])
@permission_classes([AllowAny])
def google_login(request):
    data = request.data
    users_logger.debug(f"Received data in Google login request: {data}")

    email = data.get('email')
    google_user_id = data.get('googleUserId')
    name = data.get('name', '')
    gender = data.get('gender')
    birth_date = data.get('birth_date')

    if not email or not google_user_id:
        users_logger.warning("Required Google user information missing.")
        return Response({'success': False, 'message': 'User information missing.'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        first_name, last_name = (name.split()[0], name.split()[-1]) if name else ("", "")

        # Check if a user with the same email already exists
        user, created = CustomUser.objects.get_or_create(email=email, defaults={
            'first_name': first_name,
            'last_name': last_name,
            'username': email,
        })

        if created:
            # New user was created
            Talent.objects.create(
                user=user,
                gender=gender,
                birth_date=birth_date
            )
            users_logger.info(f"New user created: {email}")
            message = "New user created. Please complete your profile."
            missing_info = True
        else:
            # User already exists, handle as an existing user login
            users_logger.info(f"Existing user logged in: {email}")
            message = "User logged in successfully."
            missing_info = False

        # Calculate age if birth_date is available
        age = None
        if birth_date:
            birth_date_obj = datetime.strptime(birth_date, '%Y-%m-%d')
            today = datetime.today()
            age = today.year - birth_date_obj.year - ((today.month, today.day) < (birth_date_obj.month, birth_date_obj.day))

        refresh = RefreshToken.for_user(user)
        refresh['user_type'] = 'Talent'
        refresh['first_name'] = user.first_name
        refresh['last_name'] = user.last_name
        refresh['username'] = user.email

        access_token = str(refresh.access_token)
        refresh_token = str(refresh)

        users_logger.debug(f"JWT tokens generated for user: {user.email} with access token: {access_token}")

        return Response({
            'success': True,
            'message': message,
            'access': access_token,
            'refresh': refresh_token,
            'email': user.email,
            'first_name': str(user.first_name).capitalize(),
            'last_name': str(user.last_name).capitalize(),
            'gender': gender,
            'age': age,

            'missing_info': missing_info,
        }, status=status.HTTP_201_CREATED)

    except IntegrityError as e:
        users_logger.error(f"Integrity error: {str(e)}")
        return Response({'success': False, 'message': 'A user with this email already exists.'}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        users_logger.exception(f"Unexpected error during Google login: {str(e)}")
        return Response({'success': False, 'message': 'An unexpected error occurred.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def complete_profile(request):
    if not request.user.is_authenticated:
        return Response({'success': False, 'message': 'Authentication required.'}, status=status.HTTP_401_UNAUTHORIZED)
    
    serializer = CompleteProfileSerializer(instance=request.user, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        print(f"Serialized data: {serializer.data}")  # Debugging line to check returned data
        return Response({'success': True}, status=status.HTTP_201_CREATED)
    else:
        return Response({'success': False, 'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

#----------------------------------------------services--------------------------------------------------------
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def check_auth(request):
    users_logger.info({"message": "User is authenticated", "user_id": request.user.id})
    print(request.user.id)
    return Response({"message": "User is authenticated", "user_id": request.user.id})





@api_view(['POST'])
@permission_classes([AllowAny])
def get_user(request):
    email = request.data.get('email')
    if not email:
        users_logger.warning("Password reset requested without providing an email.")
        return Response({"error": "Email is required."}, status=400)

    try:
        # Fetch the user by email
        user = CustomUser.objects.get(email=email)
        users_logger.info(f"User found for email: {email}")
    except ObjectDoesNotExist:
        users_logger.warning(f"User not found for email: {email}")
        return Response({"error": "User with this email does not exist."}, status=404)

    # Generate password reset token and UID
    token = default_token_generator.make_token(user)
    uid = urlsafe_base64_encode(force_bytes(user.pk))

    # Return user data
    return Response({
        "uid": uid,
        "token": token,
        "first_name": user.first_name,
    }, status=200)


@api_view(['POST'])
@permission_classes([AllowAny])
def validate_reset_token(request):
    email = request.data.get('email')
    token = request.data.get('token')

    if not email or not token:
        return Response({"error": "Email and token are required."}, status=400)

    try:
        user = CustomUser.objects.get(email=email)
        if default_token_generator.check_token(user, token):
            return Response({"message": "Token is valid."}, status=200)
        else:
            return Response({"error": "Invalid or expired token."}, status=400)
    except CustomUser.DoesNotExist:
        return Response({"error": "User does not exist."}, status=404)


@api_view(['PUT'])
@permission_classes([AllowAny])
def reset_password(request):
    email = request.data.get('email')
    new_password = request.data.get('newPassword')

    if not email or not new_password:
        return Response({"error": "Email and new password are required."}, status=400)

    try:
        user = CustomUser.objects.get(email=email)
        user.set_password(new_password)
        user.save()
        return Response({"message": "Password has been reset successfully."}, status=200)
    except CustomUser.DoesNotExist:
        return Response({"error": "User does not exist."}, status=404)
    except Exception as e:
        return Response({"error": "An error occurred while resetting the password."}, status=500)

@api_view(['GET'])
@permission_classes([IsAuthenticated])  # Or use custom permissions for service accounts
def get_inactive_users(request):
    """Endpoint to get users who haven't logged in for 72 hours."""
    threshold = timezone.now() - datetime.timedelta(hours=72)
    inactive_users = CustomUser.objects.filter(last_login__lt=threshold, is_active=True)

    serializer = CustomUserSerializer(inactive_users, many=True)
    return Response(serializer.data, status=200)



@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_talents(request):
    # Retrieve talents who are open to work
    talents = Talent.objects.filter(is_open_to_work=True, )
    serializer = TalentSerializer(talents, many=True)
    return Response(serializer.data, status=200)





# Path to your client_secret.json (downloaded from Google Cloud)
CLIENT_SECRET_FILE = os.path.join(settings.BASE_DIR, 'client_secret.json')
SCOPES = ['https://www.googleapis.com/auth/calendar']


def google_calendar_auth(request):
    try:
        flow = Flow.from_client_secrets_file(
            CLIENT_SECRET_FILE,
            scopes=SCOPES,
            redirect_uri=f"{USERS_SERVICE_URL}auth/redirect"
        )
        auth_url, _ = flow.authorization_url(access_type='offline',prompt='consent')
        users_logger.info(f"Generated OAuth URL: {auth_url}")
        return HttpResponseRedirect(auth_url)
    except Exception as e:
        users_logger.error(f"Error generating OAuth URL: {e}")
        return JsonResponse({"error": "Failed to initiate OAuth flow"}, status=500)



# def google_calendar_callback(request):
#     code = request.GET.get('code')
#     if not code:
#         return JsonResponse({'error': 'No authorization code provided'}, status=400)

#     try:
#         flow = Flow.from_client_secrets_file(
#             CLIENT_SECRET_FILE,
#             scopes=SCOPES,
#             redirect_uri="http://localhost:8000/api/v1/users/auth/redirect"
#         )
#         flow.fetch_token(code=code)
#         credentials = flow.credentials

#         print(f"Access Token: {credentials.token}")
#         print(f"Refresh Token: {credentials.refresh_token}")
#         print(f"Expiry: {credentials.expiry}")

#         # Generate the redirect URL with tokens
#         redirect_url = f"http://localhost:5173/recruiter/calendar?{urlencode({'access_token': credentials.token, 'refresh_token': credentials.refresh_token, 'expiry': credentials.expiry.isoformat()})}"

#         return HttpResponseRedirect(redirect_url)
#     except Exception as e:
#         print(f"Error in OAuth callback: {e}")
#         return JsonResponse({"error": f"Failed to complete OAuth flow: {str(e)}"}, status=500)
# import json
# import os

# CLIENT_SECRET_FILE_PATH = os.path.join(settings.BASE_DIR, 'client_secret.json')

# # Load client secret JSON
# with open(CLIENT_SECRET_FILE_PATH, 'r') as file:
#     CLIENT_SECRET_DATA = json.load(file)

# def get_google_calendar_events(request):
#     try:
#         # Retrieve tokens from session
#         token = request.session.get('google_access_token')
#         refresh_token = request.session.get('google_refresh_token')

#         # Debugging: Print tokens
#         print("Access Token in Session:", token)
#         print("Refresh Token in Session:", refresh_token)

#         if not token:
#             return JsonResponse({"error": "Missing Google Calendar credentials. Please authenticate again."}, status=401)

#         credentials = Credentials(
#             token=token,
#             refresh_token=refresh_token,
#             client_id=CLIENT_SECRET_DATA['web']['client_id'],
#             client_secret=CLIENT_SECRET_DATA['web']['client_secret'],
#             token_uri="https://oauth2.googleapis.com/token",
#         )

#         if credentials.expired or not credentials.valid:
#             print("Refreshing token...")
#             credentials.refresh(Request())
#             request.session['google_access_token'] = credentials.token
#             if credentials.refresh_token:
#                 request.session['google_refresh_token'] = credentials.refresh_token
#             request.session['google_token_expiry'] = credentials.expiry.isoformat()

#         service = build('calendar', 'v3', credentials=credentials)
#         events_result = service.events().list(
#             calendarId='primary', maxResults=50, singleEvents=True, orderBy='startTime'
#         ).execute()

#         return JsonResponse({"events": events_result.get('items', [])}, safe=False)
#     except Exception as e:
#         print(f"Error fetching calendar events: {e}")
#         return JsonResponse({"error": f"Failed to fetch events: {str(e)}"}, status=500)
    
# from google.oauth2.credentials import Credentials
# from google.auth.transport.requests import Request
# from django.http import JsonResponse

# def refresh_google_token(request):
#     if request.method != "POST":
#         return JsonResponse({"error": "Invalid request method"}, status=405)

#     refresh_token = request.POST.get("refresh_token")
#     if not refresh_token:
#         return JsonResponse({"error": "Refresh token is required"}, status=400)

#     try:
#         credentials = Credentials(
#             None,
#             refresh_token=refresh_token,
#             client_id=CLIENT_SECRET_DATA['web']['client_id'],
#             client_secret=CLIENT_SECRET_DATA['web']['client_secret'],
#             token_uri="https://oauth2.googleapis.com/token",
#         )
#         credentials.refresh(Request())

#         return JsonResponse({
#             "access_token": credentials.token,
#             "expiry": credentials.expiry.isoformat()
#         })
#     except Exception as e:
#         return JsonResponse({"error": f"Failed to refresh token: {str(e)}"}, status=500)