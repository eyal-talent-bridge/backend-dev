from django.urls import path
from . import views

urlpatterns = [
    # Fetches available slots from Google Calendar and sends them to the Talent
    path('google/calendar/slots/', views.send_slots_to_talent, name='send_slots_to_talent'),
    
    # Handles the Talent's response and creates a Zoom meeting based on their selected time slot
    path('google/calendar/handle_response/', views.handle_talent_response, name='handle_talent_response'),
    path('api/zoom/callback/', views.zoom_callback, name='zoom_callback'),
]