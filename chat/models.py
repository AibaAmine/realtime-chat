from django.db import models
from django.contrib.auth import get_user_model
import uuid

User = get_user_model()


# add members field
# the relation between user and room ?
class ChatRoom(models.Model):
    room_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    room_name = models.CharField(
        max_length=255,
        unique=True,
        help_text="Unique name for the chat room (e.g, 'general','random'.)",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    description = models.TextField(blank=True, null=True)
    is_private = models.BooleanField(default=False)

    creator = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        related_name="created_chat_rooms",
        null=True,  # Allow rooms to exist without a creator
        blank=True,
    )

    # for private or group chats
    members = models.ManyToManyField(
        User,
        related_name="joined_chat_rooms",
        blank=True,
    )

    def __str__(self):
        return self.room_name

    class Meta:
        db_table = "room"


class ChatMessage(models.Model):

    message_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    room = models.ForeignKey(
        ChatRoom, on_delete=models.CASCADE, related_name="messages"
    )
    sender = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="chat_messages"
    )

    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Message by {self.sender.username} in {self.timestamp.strftime('%Y-%m-%d %H:%M')}"

    class Meta:
        ordering = ["timestamp"]  # ordering messages by time
        db_table = "message"
