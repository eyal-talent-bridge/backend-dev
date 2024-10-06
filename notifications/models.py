from django.db import models
from users.models import Talent,Job

class TalentNotificationLog(models.Model):
    talent = models.ForeignKey(Talent, on_delete=models.CASCADE)
    job = models.ForeignKey(Job, on_delete=models.CASCADE)
    notified_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('talent', 'job')  # Ensures each talent-job combination is logged only once
