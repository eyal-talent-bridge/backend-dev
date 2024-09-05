import json
from channels.generic.websocket import AsyncWebsocketConsumer
from .models import Conversation, Message
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404

User = get_user_model()

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = f'chat_{self.room_name}'

        # Retrieve or create the conversation
        self.conversation = get_object_or_404(Conversation, id=self.room_name)

        # Join the room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        # Leave the room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json['message']
        sender = self.scope['user']  # The currently authenticated user
        conversation = self.conversation

        # Ensure that the sender is either the recruiter or the talent involved in the conversation
        if sender != conversation.recruiter and sender != conversation.talent:
            return

        # Save the message to the database
        new_message = Message.objects.create(
            conversation=conversation,
            sender=sender,
            content=message
        )

        # Send message to the room group
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': message,
                'sender': sender.email,
                'created_at': str(new_message.created_at)
            }
        )

    async def chat_message(self, event):
        message = event['message']
        sender = event['sender']
        created_at = event['created_at']

        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'message': message,
            'sender': sender,
            'created_at': created_at
        }))