# chat/consumers.py
import json

from channels.generic.websocket import AsyncWebsocketConsumer
from django.contrib.auth.models import AnonymousUser
from datetime import datetime
from .models import ChatMessage, ChatRoom
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model

User = get_user_model()


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        if isinstance(self.scope["user"], AnonymousUser):
            await self.close(code=4001)  # 4001 : unauthorized
            return

        self.room_name = self.scope["url_route"]["kwargs"]["room_name"]
        self.room_group_name = f"chat_{self.room_name}"

        is_dm_room = self.room_name.startswith("dm_")

        # get the room instance or create it if its not founded
        self.room_obj = await self.get_or_create_room(
            self.room_name, is_dm_room=is_dm_room
        )

        if not self.room_obj:
            await self.close(code=4000)  # could not get /create room
            return

        # Dm specific authorization check
        if self.room_obj.is_private:
            if not await self.is_user_member_of_room(self.room_obj, self.scope["user"]):
                print(
                    f"User {self.scope['user'].username} tried to access private room {self.room_name} but is not a member."
                )
                await self.close(code=4003)  # 4003 :Forbidden access
                return

        # Join room group
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)

        await self.accept()
        print(
            f"WebSocket CONNECT /ws/chat/{self.room_name}/ [User: {self.scope['user'].username}]"
        )

        # store the user id in a redis set
        await self.add_user_to_redis_presence(
            str(self.room_obj.room_id), str(self.scope["user"].id)
        )

        # send the initial full user list to the joining clinet
        await self.send_current_room_users()

        # Broadcast User join to Others in the room
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "user.join",
                # FIX: Correctly access user ID and username from self.scope["user"]
                "user_id": str(self.scope["user"].id),
                "username": self.scope["user"].username,
            },
        )

        # send the message history to the connected room
        await self.send_message_history()

    async def disconnect(self, close_code):
        # Leave room group
        if not isinstance(self.scope["user"], AnonymousUser):  # if authorized
            await self.channel_layer.group_discard(
                self.room_group_name, self.channel_name
            )
            print(
                f"WebSocket DISCONNECT /ws/chat/{self.room_name}/ [User: {self.scope['user'].username}] Code: {close_code}"
            )

            # remove User from Redis presence
            await self.remove_user_from_redis_presence(
                str(self.room_obj.room_id), str(self.scope["user"].id)
            )

            # Broadcast User leave event to other in the room
            # notify all other clients that this user has left
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "user.leave",
                    "user_id": str(self.scope["user"].id),
                    "username": self.scope["user"].username,
                },
            )

    # Receive message from WebSocket
    async def receive(self, text_data):
        if isinstance(self.scope["user"], AnonymousUser):
            await self.send(
                text_data=json.dumps({"error": "Unauthorized to send messages."})
            )
            await self.close(code=4001)
            return

        try:
            text_data_json = json.loads(text_data)
            message_content = text_data_json.get("message")

            if not message_content:
                await self.send(
                    text_data=json.dumps({"error": "Message content is missing"})
                )
                return

            # save msg to db
            await self.save_chat_message(
                room=self.room_obj, sender=self.scope["user"], content=message_content
            )

            # Send message to room group
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "chat.message",
                    "message": message_content,
                    "sender_id": str(self.scope["user"].id),
                    "sender_username": self.scope["user"].username,
                    "timestamp": datetime.now().isoformat(),
                },
            )
        except json.JSONDecodeError:
            print(f"Received non-JSON data or malformed JSON")
            await self.send(
                text_data=json.dumps({"error": "Invalid JSON format received"})
            )
        except Exception as e:
            print(f"Error processing message :  {e}")
            await self.send(
                text_data=json.dumps({"error": f"Server error processing message: {e}"})
            )

    # Receive message from room group
    async def chat_message(self, event):
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

    # -- HELPER METHODS FOR DB OPERATIONS --

    @database_sync_to_async
    def get_or_create_room(self, room_name, is_dm_room=False):
        room = None
        created = False 
        try:
            if is_dm_room:
                room = ChatRoom.objects.get(room_name=room_name, is_private=True)

            else:
                room, created = ChatRoom.objects.get_or_create(
                    room_name=room_name,
                    defaults={
                        "creator": self.scope["user"],
                        "is_private": False,
                        "description": f"public chat room : {room_name}",
                    },
                )
            if created:
                print(
                    f"Created new chat room: {room_name} by {self.scope['user'].username}"
                )

            return room
        except Exception as e:
            print(f"Error getting/creating chat room {room_name}: {e}")
            return None

    @database_sync_to_async
    def is_user_member_of_room(self, room, user):
        if room.is_private:
            return room.members.filter(id=user.id).exists()
        return True  # public rooms are open to all authenictated users

    @database_sync_to_async
    def save_chat_message(self, room, sender, content):
        try:
            ChatMessage.objects.create(room=room, sender=sender, content=content)
            print(f"Saved message from {sender.username} to room {room.room_name}")
        except Exception as e:
            print(f"Error saving chat message : {e}")

    # method to get messages history for a room
    @database_sync_to_async
    def get_message_history(self, room, limit=50):
        return list(
            room.messages.order_by("timestamp").values(
                "sender__username", "sender__id", "content", "timestamp"
            )
        )

    # method to send messages history to a room
    async def send_message_history(self):
        history = await self.get_message_history(self.room_obj)
        for message_data in history:
            await self.send(
                text_data=json.dumps(
                    {
                        "type": "chat_message",
                        "message": message_data["content"],
                        "sender_username": message_data["sender__username"],
                        "sender_id": str(message_data["sender__id"]),
                        "timestamp": message_data["timestamp"].isoformat(),
                    }
                )
            )

            print(
                f"Sent {len(history)} historical messages to : {self.scope['user'].username } in {self.room_obj.room_name}"
            )

    # --- Handlers for user join/leave/list events (called by channel layer) ---
    async def user_join(self, event):
        """
        Handles 'user.join' events received from the channel layer.
        This event is broadcast when a user connects to the room.
        It sends a 'user_join' message to the WebSocket client.
        """
        await self.send(
            text_data=json.dumps(
                {
                    "type": "user_join",
                    "user_id": event["user_id"],
                    "username": event["username"],
                }
            )
        )

    async def user_leave(self, event):
        """
        Handles 'user.leave' events received from the channel layer.
        This event is broadcast when a user disconnects from the room.
        It sends a 'user_leave' message to the WebSocket client.
        """
        await self.send(
            text_data=json.dumps(
                {
                    "type": "user_leave",
                    "user_id": event["user_id"],
                    "username": event["username"],
                }
            )
        )

    async def room_users_list(self, event):
        """
        Handles 'room_users_list' events received from the channel layer.
        This event is sent to a newly connecting client with the initial list of users.
        It sends a 'room_users_list' message to the WebSocket client.
        """
        await self.send(
            text_data=json.dumps(
                {
                    "type": "room_users_list",
                    "users": event["users"],  # This will be the list of user dicts
                }
            )
        )

    # --- HELPER METHODS FOR REDIS PRESENCE TRACKING  ---

    def get_presence_key(self, room_id):
        """Generates the Redis key for a room's presence set."""
        return f"room:{room_id}:presence"

    async def add_user_to_redis_presence(self, room_id, user_id):
        """Adds a user's ID to the Redis Set for room presence."""
        await self.channel_layer.connection(0).sadd(
            self.get_presence_key(room_id), user_id
        )

    async def remove_user_from_redis_presence(self, room_id, user_id):
        """Removes a user's ID from the Redis Set for room presence."""
        await self.channel_layer.connection(0).srem(
            self.get_presence_key(room_id), user_id
        )

    async def get_users_from_redis_presence(self, room_id):
        """Retrieves all user IDs from the Redis Set for room presence."""
        user_ids_bytes = await self.channel_layer.connection(0).smembers(
            self.get_presence_key(room_id)
        )
        return [uid.decode("utf-8") for uid in user_ids_bytes]

    @database_sync_to_async
    def get_user_data_for_presence_list(self, user_ids):
        """Fetches username and ID for a list of user IDs from the database."""
        if not user_ids:
            return []

        users = User.objects.filter(id__in=user_ids).values("id", "username")
        return [{"id": str(user["id"]), "username": user["username"]} for user in users]

    async def send_current_room_users(self):
        """
        Sends the current list of users in the room to the connecting client.
        """
        user_ids_in_room = await self.get_users_from_redis_presence(
            str(self.room_obj.room_id)
        )
        users_data = await self.get_user_data_for_presence_list(user_ids_in_room)
        await self.send(
            text_data=json.dumps({"type": "room_users_list", "users": users_data})
        )
        print(
            f"Sent {len(users_data)} current users to {self.scope['user'].username} in {self.room_obj.room_name}"
        )
