from django.db import models
import uuid
from django.contrib.auth import get_user_model

User = get_user_model()

class Meeting(models.Model):
    MEETING_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('canceled', 'Canceled'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    recruiter = models.ForeignKey(User, on_delete=models.CASCADE, related_name='meetings',
                                  limit_choices_to={'user_type': 'Recruiter'})
    title = models.CharField(max_length=200)
    description = models.TextField()
    talent_email = models.EmailField()  # Assuming the Talent's email is sufficient to identify them
    selected_time_slot = models.JSONField()  # Store start and end times
    zoom_link = models.URLField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=MEETING_STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Meeting between {self.recruiter.email} and {self.talent_email} on {self.selected_time_slot['start']}"

    class Meta:
        verbose_name = "Meeting"
        verbose_name_plural = "Meetings"