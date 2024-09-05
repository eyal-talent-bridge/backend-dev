import logging, ssl, smtplib
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from .serializers import *
from .models import *
from .functions import scan_cv_for_job_requirements
from django.core.mail import send_mail, get_connection
from django.conf import settings
from django.shortcuts import get_object_or_404

users_logger = logging.getLogger('users')


# Actions for a specific user, based on user_type

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
            return Response({'message': 'Invalid user type'}, status=status.HTTP_400_BAD_REQUEST)
    except (Talent.DoesNotExist, Company.DoesNotExist, Recruiter.DoesNotExist):
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
        return Response(combined_data)

    elif request.method == 'PUT':
    # Separate user data and profile data
        user_data = request.data.pop('user', None)  # Pop user-related fields if present

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
        user.delete()  # This deletes both the CustomUser profile 
        users_logger.debug(f"User {user.email} deleted successfully.")
        return Response({'message': 'User deleted successfully'}, status=status.HTTP_204_NO_CONTENT)



@api_view(['POST', 'DELETE'])
@permission_classes([IsAuthenticated])
def manage_cv(request):
    try:
        # Get the authenticated user
        user = CustomUser.objects.get(email=request.user.email)
        
        # Check if the user is a Talent and has a Talent profile
        try:
            talent = Talent.objects.get(user=user)
        except Talent.DoesNotExist:
            return Response({'message': 'Talent profile not found'}, status=status.HTTP_404_NOT_FOUND)

        # Handle POST request for uploading CV
        if request.method == 'POST':
            if 'cv' not in request.FILES:
                return Response({'message': 'No CV file provided'}, status=status.HTTP_400_BAD_REQUEST)
            
            # Upload the new CV
            talent.cv = request.FILES['cv']
            talent.save()
            users_logger.debug(f"CV saved for {user.email}")
            return Response({'message': 'CV uploaded successfully!'}, status=status.HTTP_200_OK)
        
        # Handle DELETE request for deleting CV
        elif request.method == 'DELETE':
            if talent.cv:
                talent.cv.delete()
                talent.save()
                users_logger.debug(f"CV deleted for {user.email}")
                return Response({'message': 'CV deleted successfully!'}, status=status.HTTP_200_OK)
            else:
                users_logger.debug(f"No CV to delete for {user.email}")
                return Response({'message': 'No CV to delete'}, status=status.HTTP_404_NOT_FOUND)

    except CustomUser.DoesNotExist:
        return Response({'message': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        users_logger.error(f"Error managing CV for {request.user.email}: {str(e)}")
        return Response({'message': str(e)}, status=status.HTTP_400_BAD_REQUEST)




@api_view(['POST', 'DELETE'])
@permission_classes([IsAuthenticated])
def manage_recommendation_letter(request):
    try:
        # Get the authenticated user
        user = CustomUser.objects.get(email=request.user.email)
        
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
@permission_classes([IsAuthenticated])
@api_view(['GET'])
def company_recruiters(request, company_id):
    try:
        # Fetch the company using the provided company_id
        company = Company.objects.filter(user_id=company_id).first()
        users_logger.debug("Company found successfully.")
    except Company.DoesNotExist:
        users_logger.debug(f'Company with ID {company_id} not found.')
        return Response({'message': 'Company not found'}, status=status.HTTP_404_NOT_FOUND)

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


# Check job requirements against talents
@permission_classes([IsAuthenticated])
@api_view(['GET'])
def check_requirements(request, job_id):
    try:
        job = Job.objects.get(id=job_id)
    except Job.DoesNotExist:
        users_logger.debug("Job not found, status 404.")
        return Response({'message': 'Job not found'}, status=status.HTTP_404_NOT_FOUND)

    talents = Talent.objects.all()

    relevant_talents = []  # Collect relevant talents here

    for talent in talents:
        points = 0
        total_characteristics = 2  # Initial: (is open to work & job sitting)
        matched_requirements = 0

        # Check if talent is open to work
        if talent.is_open_to_work:
            points += 1

        # Check job sitting compatibility
        if talent.job_sitting.lower() == job.job_sitting.lower():
            points += 1

        # Convert job requirements to a list of requirements if necessary
        job_requirements = [req.strip().lower() for req in job.requirements.split(',')]

        # Check skills against job requirements
        talent_skills = [skill.strip().lower() for skill in talent.skills.split(',')]
        for skill in talent_skills:
            if skill in job_requirements:
                points += 1
                matched_requirements += 1

        # Check languages against job requirements
        talent_languages = [language.strip().lower() for language in talent.languages.split(',')]
        for language in talent_languages:
            if language in job_requirements:
                points += 1
                matched_requirements += 1

        total_characteristics += len(job_requirements) + 2

        # Additional check: scan CV for job requirements
        cv_matches = scan_cv_for_job_requirements(talent.cv, job_requirements)

        match_by_form = (float(points) / total_characteristics) * 100
        match_by_cv = (float(cv_matches) / total_characteristics) * 100

        # Check if the talent meets the threshold for relevance
        if match_by_cv >= 80 or match_by_form >= 80:
            relevant_talents.append({
                'talent_id': talent.id,
                'points': points,
                'cv_matches': cv_matches,
                'match_by_form': match_by_form,
                'match_by_cv': match_by_cv
            })

    return Response({
        'relevant_talents': relevant_talents
    }, status=status.HTTP_200_OK)


# Contact Us endpoint
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def contact_us(request):
    first_name = request.data.get('first_name')
    last_name = request.data.get('last_name')
    email = request.data.get('email')
    subject = request.data.get('subject')
    message = request.data.get('message')

    if not all([first_name, last_name, email, subject, message]):
        return Response({'message': 'All fields are required.'}, status=status.HTTP_400_BAD_REQUEST)

    full_name = f"{first_name} {last_name}"
    email_subject = f"Contact Us: {subject}"
    email_message = f"From: {full_name}\nEmail: {email}\n\nMessage:\n{message}"

    try:
        if settings.DEBUG:
            context = ssl.create_default_context()
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE

            connection = get_connection()
            connection.ssl_context = context  # Apply the custom SSL context
        else:
            connection = get_connection()

        send_mail(
            email_subject,
            email_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[settings.DEFAULT_FROM_EMAIL],
            fail_silently=False,
            connection=connection,
        )
        return Response({'success': 'Email sent successfully!'}, status=status.HTTP_200_OK)
    except smtplib.SMTPException as e:
        return Response({'message': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    except Exception as e:
        return Response({'message': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@permission_classes([IsAuthenticated])
@api_view(['GET', 'PUT', 'DELETE'])
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
    
    users_logger.debug(f'Invalid request method: {request.method}')
    return Response({'message': 'Invalid request method'}, status=status.HTTP_405_METHOD_NOT_ALLOWED)





@api_view(['GET'])
@permission_classes([IsAuthenticated])
def company_jobs(request, company_id):
    # Fetch the jobs associated with the company, company_id is UUID
    jobs = Job.objects.filter(company_id=company_id)  # This will return all jobs for the company
    
    # Check if any jobs exist
    if jobs.exists():
        serializer = JobSerializer(jobs, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    else:
        return Response({"message": "No jobs found for this company"}, status=status.HTTP_404_NOT_FOUND)




@permission_classes([IsAuthenticated])
@api_view(['POST'])
def create_job(request, company_id):
    users_logger.debug(f'Create job request initiated by user: {request.user}')

    try:
        # Attach the company_id to the job data
        job_data = request.data.copy()
        job_data['company'] = company_id

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
    