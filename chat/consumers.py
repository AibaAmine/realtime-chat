# chat/consumers.py
import json
import uuid
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.utils import timezone
from .models import MessageReadStatus


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = self.scope["url_route"]["kwargs"]["room_name"]
        self.room_group_name = f"chat_{self.room_name}"

        # Join room group
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message_type = text_data_json.get("type", "message")
        
        if message_type == "read_status":
            message_id = text_data_json.get("message_id")
            username = (
                self.scope["user"].username
                if self.scope["user"].is_authenticated
                else "Anonymous"
            )
            
            # Save read status
            await self.save_read_status(message_id, username)
            
            # Send read status to room group
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "read_status_update",
                    "message_id": message_id,
                    "username": username,
                    "timestamp": timezone.now().isoformat(),
                },
            )
            return

        message = text_data_json["message"]
        username = (
            self.scope["user"].username
            if self.scope["user"].is_authenticated
            else "Anonymous"
        )
        
        # Generate unique message ID
        message_id = str(uuid.uuid4())

        await self.save_message(username, message)

        # Send message to room group
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "chat_message",
                "message": message,
                "username": username,
                "message_id": message_id,
                "timestamp": timezone.now().isoformat(),
            },
        )

    async def chat_message(self, event):
        # Send message to WebSocket
        await self.send(
            text_data=json.dumps(
                {
                    "message": event["message"],
                    "username": event["username"],
                    "message_id": event["message_id"],
                    "timestamp": event["timestamp"],
                }
            )
        )

    async def read_status_update(self, event):
        # Send read status to WebSocket
        await self.send(
            text_data=json.dumps(
                {
                    "type": "read_status",
                    "message_id": event["message_id"],
                    "username": event["username"],
                    "timestamp": event["timestamp"],
                }
            )
        )

    @database_sync_to_async
    def save_message(self, username, message):
        # Placeholder for saving messages
        pass

    @database_sync_to_async
    def save_read_status(self, message_id, username):
        if self.scope["user"].is_authenticated:
            MessageReadStatus.objects.create(
                message_id=message_id,
                room_name=self.room_name,
                user=self.scope["user"]
            )
