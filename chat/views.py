from django.http import HttpResponseForbidden
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import *
from users.models import *
from .serializers import ConversationSerializer, MessageSerializer
from django.shortcuts import render, get_object_or_404
import logging




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









