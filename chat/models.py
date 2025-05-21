from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class MessageReadStatus(models.Model):
    message_id = models.CharField(max_length=255)  # Store message identifier
    room_name = models.CharField(max_length=255)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    read_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('message_id', 'user')
