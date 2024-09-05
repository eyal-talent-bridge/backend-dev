from django.http import HttpResponseForbidden
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import *
from users.models import *
from .serializers import ConversationSerializer, MessageSerializer
from django.shortcuts import render, get_object_or_404
from rest_framework import status
import logging
from django.core.mail import send_mail
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import validate_email

notifications_logger = logging.getLogger('notifications')


# start chat with talent
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def start_conversation(request, talent_id):
    if not request.user.is_recruiter:
        return Response({'detail': 'Only recruiters can start a conversation.'}, status=403)
    
    try:
        talent = Talent.objects.filter(id=talent_id).first()
        if talent.is_talent:
            # Check if a conversation already exists between the recruiter and talent
            conversation, created = Conversation.objects.get_or_create(
                recruiter=request.user, 
                talent=talent
            )
            if created:
                return Response(ConversationSerializer(conversation).data, status=201)
            else:
                return Response({'detail': 'Conversation already exists.'}, status=200)
        else:
            return Response({'detail': 'The specified user is not a talent.'}, status=400)
    except CustomUser.DoesNotExist:
        return Response({'detail': 'Talent not found.'}, status=404)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def send_message(request, conversation_id):
    try:
        conversation = Conversation.objects.get(id=conversation_id)
        if request.user not in [conversation.recruiter, conversation.talent]:
            return Response({'detail': 'You are not part of this conversation.'}, status=403)
        
        message = Message.objects.create(
            conversation=conversation,
            sender=request.user,
            content=request.data.get('content')
        )
        return Response(MessageSerializer(message).data, status=201)
    except Conversation.DoesNotExist:
        return Response({'detail': 'Conversation not found.'}, status=404)



@api_view(['GET'])
@permission_classes([IsAuthenticated])
def conversation_list(request):
    if request.user.is_recruiter:
        conversations = Conversation.objects.filter(recruiter=request.user)
    else:
        conversations = Conversation.objects.filter(talent=request.user)
    
    serializer = ConversationSerializer(conversations, many=True)
    return Response(serializer.data, status=200)


def chat_room(request, room_name):
    conversation = get_object_or_404(Conversation, id=room_name)
    if request.user not in [conversation.recruiter, conversation.talent]:
        return HttpResponseForbidden('You are not authorized to access this chat room.')
    
    return render(request, 'chat/chat_room.html', {
        'room_name': room_name,
        'conversation': conversation
    })





# support


notifications_logger = logging.getLogger('notifications')

@permission_classes([IsAuthenticated])
@api_view(['POST'])
def mail_support(request):
    try:
        subject = request.data.get('subject')
        message = request.data.get('message')
        email = request.data.get('email')
        first_name = request.data.get('firstName')
        last_name = request.data.get('lastName')

        # Basic validation
        if not subject or not message or not email:
            return Response({"error": "Subject, message, and email are required."}, status=status.HTTP_400_BAD_REQUEST)

        # Validate email format
        try:
            validate_email(email)
        except ValidationError:
            return Response({"error": "Invalid email format."}, status=status.HTTP_400_BAD_REQUEST)

        recipient_email = 'Support@talent-bridge.org'

        # Append the sender's email and name to the message
        full_message = f"From: {first_name} {last_name} <{email}>\n\n{message}"

        send_mail(subject, full_message, settings.DEFAULT_FROM_EMAIL, [recipient_email], fail_silently=False)
        notifications_logger.debug(f"Email support sent successfully from {email} with subject '{subject}'.")
        return Response({"message": f"Email sent successfully to {recipient_email}."}, status=status.HTTP_200_OK)
    except Exception as e:
        notifications_logger.error(f"Failed to send email from {email}. Error: {str(e)}")
        return Response({"error": f"Failed to send email from {email}. Error: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
