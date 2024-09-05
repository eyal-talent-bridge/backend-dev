from django.urls import path
from .views import *

urlpatterns = [
    # URL for starting a conversation (Recruiter only)
    path('start-conversation/<uuid:talent_id>/', start_conversation, name='start_conversation'),

    # URL for sending a message in a conversation
    path('send-message/<uuid:conversation_id>/', send_message, name='send_message'),

    # URL for listing conversations (for the logged-in user, either Recruiter or Talent)
    path('conversations/', conversation_list, name='conversation_list'),

    # URL for accessing a specific chat room
    path('chat-room/<uuid:room_name>/', chat_room, name='chat_room'),

    path('support/',mail_support, name = 'mail_support')
]