import uuid
from django.db import models
from django.contrib.auth import get_user_model
from users.models import *

CustomUser = get_user_model()

class Conversation(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    recruiter = models.ForeignKey(Recruiter, on_delete=models.CASCADE, related_name='started_conversations')
    talent = models.ForeignKey(Talent, on_delete=models.CASCADE, related_name='received_conversations')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Conversation between {self.recruiter.email} and {self.talent.email}"

class Message(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Message from {self.sender.email} at {self.created_at}"