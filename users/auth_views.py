import logging
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate, login as auth_login, logout as logout_method
from rest_framework_simplejwt.views import TokenObtainPairView
from .serializers import *
from .models import CustomUser
from django.core.mail import send_mail,BadHeaderError
from django.conf import settings
from social_django.utils import psa
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth.hashers import make_password
from .functions import *
from uuid import UUID


auth_logger = logging.getLogger('auth')

class MyTokenObtainPairView(TokenObtainPairView):
    serializer_class = MyTokenObtainPairSerializer



@api_view(['POST'])
def signin(request):
    try:
        # Get email and password from request data
        data = request.data
        username = data.get('email', '').lower().strip()
        password = data.get('password', '').strip()

        auth_logger.debug(f'Attempting login for user: {username}')

        # Authenticate user using email as the username
        user = authenticate(request, username=username, password=password)

        if user is not None:
            auth_logger.debug(f'User authenticated: {user.username}')
            user_type = user.user_type
            first_name = user.first_name
            last_name = user.last_name if user_type != 'Company' else ''
            name = user.name if user_type == 'Company' else f"{first_name} {last_name}"

            # Log in the user (start the session)
            auth_login(request, user)

            # Create refresh token and add custom claims
            refresh = RefreshToken.for_user(user)
            refresh['user_type'] = user_type
            refresh['first_name'] = first_name
            refresh['last_name'] = last_name
            refresh['name'] = name
            refresh['user_id'] = str(user.id)

            # Include company_id if the user is a Recruiter and belongs to a company
            if user_type == 'Recruiter' and hasattr(user, 'company'):
                refresh['company_id'] = str(user.company.id)

            access = refresh.access_token

            auth_logger.debug(f'{username} logged in as {user_type}')

            # Return the JWT tokens
            return Response({
                'refresh': str(refresh),
                'access': str(access)
            }, status=status.HTTP_200_OK)

        else:
            # If authentication fails
            auth_logger.debug(f'Invalid login attempt for email: {username}')
            return Response({'status': 'error', 'message': 'Invalid email or password'}, status=status.HTTP_401_UNAUTHORIZED)

    except Exception as e:
        # If any other error occurs
        auth_logger.error(f'Error logging in: {str(e)}')
        return Response({'status': 'error', 'message': 'An error occurred during login'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@psa('social:complete')
def talent_facebook_login(request, backend):
    user = request.backend.do_auth(request.data.get('access_token'))

    if user and user.is_active:
        details = request.data.get('user_details', {})

        # Create or update the user instance
        for field, value in details.items():
            setattr(user, field, value)
        user.save()

        # Create and return JWT tokens
        refresh = RefreshToken.for_user(user)
        return Response({
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'message': f'{user.user_type} profile updated successfully'
        })
    else:
        return Response({'error': 'Authentication Failed'}, status=status.HTTP_400_BAD_REQUEST)


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

            if not validate_company_email(email=email):
                return Response({'error': 'Invalid company email'}, status=status.HTTP_400_BAD_REQUEST)
            
            if not validate_company_website(website=website):
                return Response({'error': 'Invalid company website'}, status=status.HTTP_400_BAD_REQUEST)

            if not validate_phone_number(phone_number):
                return Response({'error': 'Invalid company phone number'}, status=status.HTTP_400_BAD_REQUEST)

            # password validation
            # if not validate_password(password):
            #     return Response({'error': 'Invalid password'}, status=status.HTTP_400_BAD_REQUEST)

            # Create the CustomUser instance 
            user = CustomUser.objects.create_user(
                username=email,  # Use email as the username
                email=email,
                password=make_password(password),  # Hash the password
                user_type=user_type,
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
                company_id = UUID(request.data.get('company'))
                print(f"Company ID (UUID): {company_id}")  # Debugging line to print the company_id
            except ValueError:
                return Response({'message': 'Invalid company ID'}, status=status.HTTP_400_BAD_REQUEST)

            gender = request.data.get('gender')
            phone_number = request.data.get('phone_number')

            # Validate recruiter's email against the company's email domain
            if not validate_recruiter_email(email, company_id):
                return Response({'message': 'Invalid recruiter email'}, status=status.HTTP_400_BAD_REQUEST)

            # Validate phone number format
            if not validate_phone_number(phone_number):
                return Response({'message': 'Invalid recruiter phone number'}, status=status.HTTP_400_BAD_REQUEST)

            # Fetch the company using the company ID
            try:
                company = Company.objects.filter(user_id=company_id).first()
                print(f"Company Found")  # Debugging line to confirm the company is fetched

            except Company.DoesNotExist:
                print(f"Company with ID {company_id} not found")  # Debugging line if company not found
                return Response({'message': 'Company not found'}, status=status.HTTP_404_NOT_FOUND)

            # Create the CustomUser instance with first and last name
            user = CustomUser.objects.create_user(
                username=email,  # Use email as the username
                email=email,
                password=make_password(password),  # Hash the password
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

            # password validation
            if not validate_phone_number(phone_number):
                return Response({'message': 'Invalid company phone number'}, status=status.HTTP_400_BAD_REQUEST)
            
            if not validate_talent_email():
                return Response({"message": "Invalid email for Talent"}, status=status.HTTP_400_BAD_REQUEST)

            # Create the CustomUser instance with first and last name
            user = CustomUser.objects.create_user(
                username=email,  # Use email as the username
                email=email,
                password=make_password(password),  # Hash the password
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
        refresh['last_name'] = last_name if user_type != 'Company' else ''
        refresh['user_id'] = str(user.id)

        access = refresh.access_token

        # Log the creation of the user
        auth_logger.debug(f'{email} created successfully as {user_type}')
        
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
        auth_logger.error(f"Error creating user: {e}")
        return Response({"message": "An error occurred while creating the user."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)





@api_view(['POST'])
def talent_signup(request):
    return user_signup(request, 'Talent')


@api_view(['POST'])
def recruiter_signup(request):
    return user_signup(request, 'Recruiter')


@api_view(['POST'])
def company_signup(request):
    return user_signup(request, 'Company')


# --------------------------Password Handling------------------------------------------------------------
@api_view(['POST'])
@permission_classes([AllowAny])
def request_password_reset(request):
    email = request.data.get('email')
    if not email:
        auth_logger.warning("Password reset requested without providing an email.")
        return Response({"message": "Email is required."}, status=400)

    try:
        user = CustomUser.objects.get(email=email)
        auth_logger.info(f"Password reset request received for existing user: {email}.")
    except CustomUser.DoesNotExist:
        auth_logger.warning(f"Password reset attempted for non-existent user with email: {email}.")
        return Response({"message": "User with this email does not exist."}, status=404)

    token = default_token_generator.make_token(user)
    reset_link = f"{settings.FRONTEND_URL}/auth/reset-password/{token}/?email={email}"

    email_subject = "Password Reset Request - Talent-Bridge"
    email_body = (
        f"Dear {user.first_name},\n\n"
        f"We received a request to reset your password for your Talent-Bridge account associated with this email address. "
        f"If you made this request, please click the link below to reset your password:\n\n"
        f"{reset_link}\n\n"
        f"For security reasons, this link will expire in 24 hours. "
        f"If you did not request a password reset, please ignore this email or contact our support team if you have any concerns.\n\n"
        f"Thank you for using Talent-Bridge.\n\n"
        f"Best regards,\n"
        f"The Talent-Bridge Team"
    )

    try:
        send_mail(
            email_subject,
            email_body,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
        )
    except BadHeaderError:
        auth_logger.error(f"BadHeaderError: Invalid header encountered when sending email to {email}.")
        return Response({"error": "Invalid header found."}, status=400)
    except Exception as e:
        auth_logger.error(f"Error sending email to {email}: {e}")
        return Response({"error": "An error occurred while sending the email."}, status=500)

    auth_logger.info(f"Password reset link successfully sent to {email}.")
    return Response({"message": "Password reset link sent."}, status=200)


@api_view(['PUT'])
@permission_classes([AllowAny])
def reset_password_confirm(request, token):
    email = request.data.get('email')
    new_password = request.data.get('newPassword')

    auth_logger.info(f"Password reset request received with token: {token}")

    if not email or not new_password:
        auth_logger.warning("Email or new password not provided.")
        return Response({"error": "Email and new password are required."}, status=status.HTTP_400_BAD_REQUEST)

    try:
        user = CustomUser.objects.get(email=email)
    except CustomUser.DoesNotExist:
        auth_logger.warning(f"User with email {email} does not exist.")
        return Response({"error": "Invalid email."}, status=status.HTTP_404_NOT_FOUND)

    # Validate token and reset the password
    if default_token_generator.check_token(user, token):
        try:
            user.set_password(new_password)
            user.save()

            auth_logger.info(f"Password reset successfully for user with email: {user.email}")
            return Response({"message": "Password has been reset successfully."}, status=status.HTTP_200_OK)

        except Exception as e:
            auth_logger.error(f"Error saving new password for user with email {user.email}: {e}")
            return Response({"error": "An error occurred while resetting the password."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    else:
        auth_logger.warning(f"Invalid or expired token for user with email: {email}")
        return Response({"error": "Invalid or expired token."}, status=status.HTTP_400_BAD_REQUEST)

# --------------------------Logout------------------------------------------------------------------------------------------------------------

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout(request):
    logout_method(request)
    auth_logger.debug(f"User {request.user.email} logged out.")
    return Response({"message": "User logged out successfully."}, status=status.HTTP_200_OK)


