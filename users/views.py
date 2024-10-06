import logging
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from .serializers import *
from .models import *
import datetime
from .utils import scan_cv_for_job_requirements
from notifications.utils import appear_on_job_search_notification
from django.shortcuts import get_object_or_404
users_logger = logging.getLogger('users')

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
        user.delete()
        return Response({'message': 'User deleted successfully'}, status=status.HTTP_204_NO_CONTENT)
    

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




@api_view(['GET', 'PUT', 'DELETE'])
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
    
    users_logger.debug(f'Invalid request method: {request.method}')
    return Response({'message': 'Invalid request method'}, status=status.HTTP_405_METHOD_NOT_ALLOWED)





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
@permission_classes([IsAuthenticated])
def manage_recruiters(request, recruiter_id):
    users_logger.debug(f'Request method: {request.method}, Recruiter ID: {recruiter_id}, User: {request.user}')

    # Try to find the recruiter
    recruiter = Recruiter.objects.filter(id=recruiter_id).first()
    if not recruiter:
        users_logger.debug(f'Recruiter not found: {recruiter_id}')
        return Response({'message': 'Recruiter not found'}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        # Get the user and profile data
        user_serializer = CustomUserSerializer(recruiter.user)  # Assuming Recruiter has a related CustomUser
        recruiter_serializer = RecruiterSerializer(recruiter)  # Assuming Recruiter has a related Profile

        # Combine both serialized data
        combined_data = {**user_serializer.data, **recruiter_serializer.data}
        users_logger.debug(f'Recruiter data retrieved: {combined_data}')
        return Response(combined_data, status=status.HTTP_200_OK)

    elif request.method == 'PUT':
        serializer = RecruiterSerializer(recruiter, data=request.data)
        if serializer.is_valid():
            serializer.save()
            users_logger.debug(f'Recruiter updated successfully: {serializer.data}')
            return Response(serializer.data, status=status.HTTP_200_OK)
        users_logger.debug(f'Recruiter update failed: {serializer.errors}')
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'DELETE':
        recruiter.delete()
        users_logger.debug(f'Recruiter deleted successfully: {recruiter_id}')
        return Response({'message': 'Recruiter deleted successfully!'}, status=status.HTTP_200_OK)

    users_logger.debug(f'Invalid request method: {request.method}')
    return Response({'message': 'Invalid request method'}, status=status.HTTP_405_METHOD_NOT_ALLOWED)




@api_view(['GET'])
@permission_classes([IsAuthenticated])
def search_talents_for_job(request, job_id):
    try:
        # Get the job object
        job = get_object_or_404(Job, id=job_id)
        company = job.company
        
        # Check if the job is relevant and active
        if job.is_relevant and job.end_date >= datetime.datetime.now().date() :
            users_logger.info(f"Starting talent search for job: {job.title} at company: {company.name}")

            # Log the number of talents found
            talents = Talent.objects.filter(is_open_to_work=True)
            # .exclude(companies_black_list__contains=job.company)
            users_logger.info(f"{talents.count()} talents found who are open to work for job - {job.title} in {company.name}.")

            # Initialize job requirements list
            job_requirements = []

            # Extracting job requirements with explicit type handling
            if isinstance(job.requirements, list):
                job_requirements = [req.strip().lower() for req in job.requirements if isinstance(req, str)]
            elif isinstance(job.requirements, str):
                job_requirements = [req.strip().lower() for req in job.requirements.split(',')]
            elif isinstance(job.requirements, dict):
                for key, value in job.requirements.items():
                    if isinstance(value, str):
                        job_requirements.extend([req.strip().lower() for req in value.split(',') if req])
                    elif isinstance(value, list):
                        job_requirements.extend([req.strip().lower() for req in value if isinstance(req, str)])
                    else:
                        users_logger.warning(f"Unexpected type for requirement value under key '{key}': {type(value)}")
            else:
                users_logger.error(f"Unexpected type for job requirements: {type(job.requirements)}")
                return Response({'message': 'Invalid job requirements format'}, status=status.HTTP_400_BAD_REQUEST)

            users_logger.info(f"Extracted job requirements: {job_requirements}")

            total_characteristics = 1 + len(job_requirements)  # Open to work plus job requirements
            relevant_talents = []

            for talent in talents:
                user = talent.user
                if not talent.is_open_to_work:
                    users_logger.info(f"Talent {talent.id} is not open to work.")
                    continue

                if not talent.cv:
                    users_logger.warning(f"Talent {talent.id} does not have a CV.")
                    continue

                points = 0
                # Matching criteria: job sitting, residence, job type
                if talent.job_sitting.lower() == job.job_sitting.lower():
                    points += 1

                if talent.residence.lower().replace(',', '') == job.location.lower().replace(',', ''):
                    points += 1

                if talent.job_type.lower() == job.job_type.lower():
                    points += 1

                # Handling talent skills and languages
                talent_skills = talent.skills if isinstance(talent.skills, list) else list(talent.skills.values())
                talent_languages = talent.languages if isinstance(talent.languages, list) else list(talent.languages.values())

                talent_qualifications = [qual.strip().lower() for qual in talent_skills + talent_languages if isinstance(qual, str)]

                matched_requirements = sum(1 for qualification in talent_qualifications if qualification in job_requirements)

                points += matched_requirements
                match_by_form = (float(points) / total_characteristics) * 100

                # Assuming scan_cv_for_job_requirements is a function that scans the CV for job requirements
                cv_matches = scan_cv_for_job_requirements(talent.cv, job_requirements)
                match_by_cv = (float(cv_matches) / total_characteristics) * 100

                users_logger.info(f"Talent {talent.id} match by form: {match_by_form}%, match by CV: {match_by_cv}%.")

                # If talent matches by either form or CV criteria, add them to the relevant talents list
                if match_by_cv >= 30 or match_by_form >= 30:
                    relevant_talents.append({
                        'user_id': user.id,
                        'username': user.email,
                        'first_name': user.first_name,
                        'last_name': user.last_name,
                        'points': points,
                        'cv_matches': cv_matches,
                        'match_by_form': round(match_by_form, 2),
                        'match_by_cv': round(match_by_cv, 2)
                    })

            # Call notification function only after all relevant talents are collected
            appear_on_job_search_notification(request, relevant_talents, job_id)

        else:
            users_logger.info("Job is not relevant.")
            return Response({"message": "Job is not relevant"}, status=status.HTTP_400_BAD_REQUEST)

        return Response({'relevant_talents': relevant_talents}, status=status.HTTP_200_OK)

    except Job.DoesNotExist:
        users_logger.error(f"Job {job_id} not found.")
        return Response({'message': 'Job not found'}, status=status.HTTP_404_NOT_FOUND)
    
    except Exception as e:
        users_logger.error(f"Error searching talents for job {job_id}: {str(e)}")
        return Response({'message': f"An error occurred while searching for talents: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)