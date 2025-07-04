# chat/consumers.py
import json

from channels.generic.websocket import AsyncWebsocketConsumer
from django.contrib.auth.models import AnonymousUser
from datetime import datetime


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        if isinstance(self.scope["user"], AnonymousUser):
            await self.close(code=4001)  # 4001 : unauthorized
            return

        self.room_name = self.scope["url_route"]["kwargs"]["room_name"]
        self.room_group_name = f"chat_{self.room_name}"

        # Join room group

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)

        await self.accept()
        print(
            f"WebSocket CONNECT /ws/chat/{self.room_name}/ [User: {self.scope['user'].username}]"
        )

    async def disconnect(self, close_code):
        # Leave room group
        if not isinstance(self.scope["user"], AnonymousUser):  # if ahthorized
            await self.channel_layer.group_discard(
                self.room_group_name, self.channel_name
            )

    # Receive message from WebSocket
    async def receive(self, text_data):
        if isinstance(self.scope["user"], AnonymousUser):
            await self.send(text_data=json.dump({"Unauthorized to send messages. "}))
            await self.close(code=4001)
            return

        text_data_json = json.loads(text_data)
        message = text_data_json.get("message")

        # Send message to room group
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "chat.message",
                "message": message,
                "sender_id": str(self.scope["user"].id),
                "sender_username": self.scope["user"].username,
                "timestamp": datetime.now().isoformat(),
            },
        )

    # Receive message from room group
    async def chat_message(self, event):
        # --- NEW DEBUG PRINT HERE ---
        print(f"DEBUG (chat_message): Received event from channel layer: {event}")
        # --- END NEW DEBUG PRINT --

        message = event["message"]
        sender_username = event.get("sender_username", "Unknown")
        sender_id = (
            str(event.get("sender_id", ""))
            if event.get("sender_id") is not None
            else None
        )
        timestamp = event.get("timestamp", "")

        # Send message to WebSocket
        await self.send(
            text_data=json.dumps(
                {
                    "type": "chat_message",
                    "message": message,
                    "sender_username": sender_username,
                    "sender_id": sender_id,
                    "timestamp": timestamp,
                }
            )
        )
