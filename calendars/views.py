# views.py
from rest_framework.response import Response
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from datetime import datetime, timedelta, time
from django.utils import timezone
import requests, json
from .tasks import send_available_slots_email, send_zoom_link_to_recruiter_and_talent
import logging,requests
from django.shortcuts import redirect
from django.conf import settings
from django.contrib.auth.decorators import login_required
from social_django.models import UserSocialAuth

calendar_logger = logging.getLogger('calendar')

# Fetches available time slots from the recruiter's Google Calendar
def get_google_calendar_events(recruiter):
    try:
        creds = Credentials.from_authorized_user(recruiter.oauth_token)
        service = build('calendar', 'v3', credentials=creds)

        now = datetime.utcnow().isoformat() + 'Z'
        events_result = service.events().list(calendarId='primary', timeMin=now, singleEvents=True, orderBy='startTime').execute()
        events = events_result.get('items', [])

        available_slots = []

        for day_offset in range(7):
            day = (datetime.utcnow() + timedelta(days=day_offset)).weekday()

            working_hours = recruiter.get_working_hours_for_day(day)
            if not working_hours:
                continue

            work_start_time = timezone.make_aware(datetime.combine(datetime.today() + timedelta(days=day_offset), time.fromisoformat(working_hours['start'])))
            work_end_time = timezone.make_aware(datetime.combine(datetime.today() + timedelta(days=day_offset), time.fromisoformat(working_hours['end'])))

            day_events = [
                event for event in events if datetime.fromisoformat(event['start']['dateTime']).date() == work_start_time.date()
            ]

            current_time = work_start_time

            for event in day_events:
                event_start = datetime.fromisoformat(event['start']['dateTime'])
                event_end = datetime.fromisoformat(event['end']['dateTime'])

                if current_time < event_start:
                    available_slot = (current_time, event_start)
                    if available_slot[1] - available_slot[0] >= timedelta(minutes=30):
                        available_slots.append(available_slot)

                current_time = event_end

            if current_time < work_end_time:
                available_slot = (current_time, work_end_time)
                if available_slot[1] - available_slot[0] >= timedelta(minutes=30):
                    available_slots.append(available_slot)

        return available_slots
    except Exception as e:
        calendar_logger.error(f"Error fetching calendar events: {e}")
        return []


# Sending time options to talent via email
def send_slots_to_talent(request):
    recruiter = request.user  # Assuming recruiter is the logged-in user
    talent_email = request.data.get("talent_email")  # Fetch talent email from request data
    if not talent_email:
        return Response({"message": "Talent email is required."}, status=400)

    available_slots = get_google_calendar_events(recruiter)

    if available_slots:
        send_available_slots_email.delay(recruiter.id, talent_email, available_slots)
        return Response({"message": "Email sent to Talent with available slots."}, status=200)
    else:
        return Response({"message": "No available slots found."}, status=404)

# Handling the talent's response with the selected slot
def handle_talent_response(request):
    selected_slot_index = int(request.data.get('selected_slot')) - 1
    talent_email = request.data.get('talent_email')

    if not talent_email:
        return Response({"message": "Talent email is required."}, status=400)

    recruiter = request.user  # Assuming recruiter is the logged-in user
    available_slots = get_google_calendar_events(recruiter)

    if 0 <= selected_slot_index < len(available_slots):
        selected_slot = available_slots[selected_slot_index]

        zoom_meeting_link = create_zoom_meeting(recruiter, selected_slot)

        if zoom_meeting_link:
            send_zoom_link_to_recruiter_and_talent.delay(recruiter.email, talent_email, zoom_meeting_link)
            return Response({"message": "Zoom meeting scheduled and link sent to both parties."}, status=201)
        else:
            return Response({"message": "Failed to create Zoom meeting."}, status=500)
    else:
        return Response({"message": "Invalid time slot selected."}, status=400)





@login_required
def zoom_callback(request):
    code = request.GET.get('code')
    if not code:
        return redirect('some-error-page')

    # Exchange the authorization code for access and refresh tokens
    token_url = "https://zoom.us/oauth/token"
    redirect_uri = "https://yourdomain.com/api/zoom/callback/"  # This must match the redirect URI set in Zoom Marketplace

    data = {
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': redirect_uri,
    }

    auth = (settings.SOCIAL_AUTH_ZOOM_OAUTH2_KEY, settings.SOCIAL_AUTH_ZOOM_OAUTH2_SECRET)

    response = requests.post(token_url, data=data, auth=auth)

    if response.status_code == 200:
        tokens = response.json()
        access_token = tokens.get('access_token')
        refresh_token = tokens.get('refresh_token')
        expires_in = tokens.get('expires_in')

        # Store the tokens in UserSocialAuth (or a custom model)
        user = request.user
        social_auth, created = UserSocialAuth.objects.get_or_create(user=user, provider='zoom-oauth2')
        social_auth.extra_data = {
            'access_token': access_token,
            'refresh_token': refresh_token,
            'expires_in': expires_in,
        }
        social_auth.save()

        return redirect('some-success-page')
    else:
        return redirect('some-error-page')



# Creating Zoom meeting based on the selected slot
def create_zoom_meeting(user, topic, start_time, duration):
    social_auth = user.social_auth.get(provider='zoom-oauth2')
    access_token = social_auth.extra_data['access_token']
    if not access_token:
        return None

    zoom_api_url = "https://api.zoom.us/v2/users/me/meetings"
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    meeting_details = {
        "topic": topic,
        "type": 2,
        "start_time": start_time.isoformat(),
        "duration": duration,
        "timezone": "UTC",
        "settings": {
            "host_video": True,
            "participant_video": True,
            "join_before_host": False,
            "mute_upon_entry": True,
        }
    }

    response = requests.post(zoom_api_url, headers=headers, data=json.dumps(meeting_details))

    if response.status_code == 201:
        return response.json()['join_url']
    else:
        return None