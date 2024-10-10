from django.db import models
from users.models import Talent,Job,Recruiter

class TalentNotificationLog(models.Model):
    talent = models.ForeignKey(Talent, on_delete=models.CASCADE)
    job = models.ForeignKey(Job, on_delete=models.CASCADE)
    notified_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('talent', 'job')  # Ensures each talent-job combination is logged only once




# models.py
from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class CompanyNotification(models.Model):
    recipient = models.ForeignKey(Recruiter, on_delete=models.CASCADE, related_name="CompanyNotification")
    subject = models.CharField(max_length=255)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    end_date = models.DateField(blank=True, null=True)
    is_read = models.BooleanField(default=False)

    def __str__(self):
        return f"Notification for {self.recipient.id} - {self.subject}"